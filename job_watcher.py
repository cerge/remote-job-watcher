"""
Remote Job Watcher
==================
Lee ofertas laborales desde RSS feeds publicos,
filtra por keywords y guarda los resultados en CSV.

Version: 1.3.0
- Feeds especificos de QA y Software Dev
- Keywords ampliadas para titulos reales
- STRICT_MODE = False (feeds remotos por naturaleza)
"""

import csv
import hashlib
import os
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime

import feedparser
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

# ─────────────────────────────────────────────────────────────
# CONFIGURACION
# ─────────────────────────────────────────────────────────────

# Keywords que se buscan SOLO EN EL TITULO.
# Ampliadas para capturar titulos reales de los feeds.
KEYWORDS_TECH = [
    # PHP / Laravel
    "PHP",
    "Laravel",
    "Backend",
    "Back-end",
    "Back End",
    "Full Stack",
    "Full-Stack",
    "Fullstack",
    # QA / Testing
    "QA",
    "Quality Assurance",
    "Tester",
    "Testing",
    "Automation",
    "Playwright",
    "SDET",
    "Test Engineer",
    "QA Engineer",
    "QA Analyst",
]

# Keywords de modalidad remota.
# Solo se usan cuando STRICT_MODE = True.
KEYWORDS_REMOTE = [
    "remote",
    "remoto",
    "remotamente",
    "trabajo remoto",
    "100% remoto",
    "distributed",
    "anywhere",
    "worldwide",
]

# False → busca KEYWORDS_TECH solo en el titulo (recomendado con feeds 100% remotos)
# True  → ademas verifica que el texto mencione modalidad remota
STRICT_MODE = False

KEYWORDS = KEYWORDS_TECH

# ─────────────────────────────────────────────────────────────
# RSS FEEDS
# ─────────────────────────────────────────────────────────────

RSS_FEEDS = [
    # ── Especificos de QA ────────────────────────────────────
    # Remotive tiene categoria propia de QA — mucho mas relevante
    {
        "name": "Remotive – QA",
        "url": "https://remotive.com/rss/remote-jobs/qa",
    },

    # ── Software Dev / Backend / Full Stack ──────────────────
    {
        "name": "Remotive – Software Dev",
        "url": "https://remotive.com/rss/remote-jobs/software-dev",
    },
    {
        "name": "We Work Remotely – Programming",
        "url": "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    },
    # Feed completo de WWR (incluye mas categorias)
    {
        "name": "We Work Remotely – All",
        "url": "https://weworkremotely.com/remote-jobs.rss",
    },
    {
        "name": "Remote OK",
        "url": "https://remoteok.com/remote-jobs.rss",
    },

    # ── Espanol / America Latina ─────────────────────────────
    {
        "name": "GetOnBoard",
        "url": "https://www.getonbrd.com/jobs.rss",
    },
    {
        "name": "Computrabajo Argentina",
        "url": "https://www.computrabajo.com.ar/rss/ofertas-de-trabajo.xml",
    },
    {
        "name": "Zonajobs",
        "url": "https://www.zonajobs.com.ar/empleos.rss",
    },
]

OUTPUT_CSV    = "resultados.csv"
ONLY_NEW_JOBS = True

# ─────────────────────────────────────────────────────────────
# MODELO DE DATOS
# ─────────────────────────────────────────────────────────────

@dataclass
class Job:
    title: str
    company: str
    url: str
    source: str
    published: str
    description: str
    matched_keywords: list
    job_id: str = field(default="")

    def __post_init__(self):
        if not self.job_id:
            raw = f"{self.title.lower()}{self.company.lower()}"
            self.job_id = hashlib.md5(raw.encode()).hexdigest()[:12]


# ─────────────────────────────────────────────────────────────
# FUNCIONES
# ─────────────────────────────────────────────────────────────

def load_seen_ids(csv_path: str) -> set:
    """Lee el CSV anterior y devuelve los IDs ya vistos."""
    seen = set()
    if not os.path.exists(csv_path):
        return seen
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if "job_id" in row:
                seen.add(row["job_id"])
    return seen


def save_jobs_to_csv(jobs: list, csv_path: str) -> int:
    """Guarda trabajos en CSV. Agrega filas, nunca sobreescribe."""
    if not jobs:
        return 0
    rows       = [asdict(job) for job in jobs]
    fieldnames = ["job_id", "title", "company", "source", "published",
                  "url", "matched_keywords", "description"]
    file_exists = os.path.exists(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        if not file_exists:
            writer.writeheader()
        for row in rows:
            row["matched_keywords"] = " | ".join(row.get("matched_keywords", []))
            writer.writerow(row)
    return len(jobs)


def fetch_feed(feed_config: dict) -> list:
    """Descarga y parsea un RSS feed. Devuelve lista vacia si falla."""
    try:
        feed = feedparser.parse(feed_config["url"])
        return feed.entries
    except Exception:
        return []


def extract_text(entry) -> str:
    """Extrae texto limpio (sin HTML) de un item del feed."""
    text = ""
    if hasattr(entry, "summary"):
        text = entry.summary
    elif hasattr(entry, "description"):
        text = entry.description
    elif hasattr(entry, "content") and entry.content:
        text = entry.content[0].value
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:300] + "..." if len(text) > 300 else text


def check_keywords(title: str, full_text: str) -> list:
    """
    Busca KEYWORDS_TECH en el titulo del trabajo.

    STRICT_MODE = False (recomendado con feeds 100% remotos):
      Solo verifica que el titulo tenga una keyword de tecnologia.
      Los feeds como Remotive y WWR ya son remotos por naturaleza.

    STRICT_MODE = True:
      Ademas verifica que el texto mencione modalidad remota.
      Util si agregás feeds generales que mezclan remoto y presencial.
    """
    title_lower    = title.lower()
    fulltext_lower = full_text.lower()

    # Siempre: tecnologia tiene que estar en el titulo
    tech_matches = [k for k in KEYWORDS_TECH if k.lower() in title_lower]

    if not tech_matches:
        return []

    if STRICT_MODE:
        # Ademas verificar modalidad remota en el texto
        remote_matches = [k for k in KEYWORDS_REMOTE if k.lower() in fulltext_lower]
        if not remote_matches:
            return []

    return tech_matches


def process_feed(feed_config: dict, seen_ids: set) -> list:
    """Procesa un feed: descarga, filtra, descarta ya vistos."""
    entries      = fetch_feed(feed_config)
    matched_jobs = []

    for entry in entries:
        title       = getattr(entry, "title",     "Sin titulo")
        company     = getattr(entry, "author",    None) or getattr(entry, "publisher", "Empresa desconocida")
        url         = getattr(entry, "link",      "")
        published   = getattr(entry, "published", "Fecha desconocida")
        description = extract_text(entry)
        full_text   = f"{title} {description}"

        matched = check_keywords(title, full_text)
        if not matched:
            continue

        job = Job(
            title=title, company=company, url=url,
            source=feed_config["name"], published=published,
            description=description, matched_keywords=matched,
        )

        if ONLY_NEW_JOBS and job.job_id in seen_ids:
            continue

        matched_jobs.append(job)

    return matched_jobs


# ─────────────────────────────────────────────────────────────
# DISPLAY
# ─────────────────────────────────────────────────────────────

def print_config_summary(console: Console) -> None:
    mode_text = "[yellow]SIMPLE[/yellow] (tech en titulo, feeds ya son remotos)" if not STRICT_MODE else "[green]ESTRICTO[/green] (tech en titulo + remoto en texto)"
    console.print(f"  [bold]Modo:[/bold]       {mode_text}")
    console.print(f"  [bold]Tecnologia:[/bold] {', '.join(KEYWORDS_TECH)}")
    console.print(f"  [bold]Feeds:[/bold]      {len(RSS_FEEDS)} configurados\n")


def print_results(jobs: list, console: Console) -> None:
    if not jobs:
        console.print("\n[yellow]No se encontraron trabajos nuevos.[/yellow]")
        console.print("[dim]Tips:[/dim]")
        console.print("[dim]  - Borra resultados.csv y volvé a correr: del resultados.csv[/dim]")
        console.print("[dim]  - Revisá que los feeds esten trayendo datos[/dim]\n")
        return

    table = Table(
        title=f"[bold cyan]💼 {len(jobs)} trabajos encontrados[/bold cyan]",
        box=box.ROUNDED, show_lines=True,
        header_style="bold white on dark_blue", expand=True,
    )
    table.add_column("#",        style="dim",            width=4,  justify="right")
    table.add_column("Titulo",   style="bold",           min_width=25)
    table.add_column("Empresa",  style="cyan",           min_width=15)
    table.add_column("Fuente",   style="magenta",        min_width=14)
    table.add_column("Keywords", style="green",          min_width=12)
    table.add_column("URL",      style="blue underline", min_width=20)

    for i, job in enumerate(jobs, start=1):
        short_url = job.url[:50] + "..." if len(job.url) > 50 else job.url
        table.add_row(
            str(i), job.title, job.company, job.source,
            ", ".join(job.matched_keywords), short_url,
        )
    console.print(table)


def print_summary(jobs: list, saved: int, console: Console) -> None:
    by_source = {}
    for job in jobs:
        by_source[job.source] = by_source.get(job.source, 0) + 1

    lines = [
        f"[bold]Fecha:[/bold]             {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        f"[bold]Total encontrados:[/bold] [green]{len(jobs)}[/green]",
        f"[bold]Guardados en CSV:[/bold]  [green]{saved}[/green] → {OUTPUT_CSV}",
        "", "[bold]Por fuente:[/bold]",
    ]
    for source, count in by_source.items():
        lines.append(f"  • {source}: [cyan]{count}[/cyan]")

    console.print(Panel(
        "\n".join(lines),
        title="[bold blue]📊 Resumen[/bold blue]",
        border_style="blue", padding=(1, 2),
    ))


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def main():
    console = Console()

    console.print(Panel(
        "[bold cyan]Remote Job Watcher[/bold cyan]  [dim]v1.3.0[/dim]\n"
        "[dim]Filtra ofertas remotas de PHP · Laravel · QA · Playwright[/dim]",
        border_style="cyan", padding=(1, 4),
    ))

    print_config_summary(console)

    seen_ids = load_seen_ids(OUTPUT_CSV)
    if seen_ids:
        console.print(f"[dim]📋 {len(seen_ids)} trabajos ya vistos (se omitiran)[/dim]\n")

    all_jobs = []
    for feed_config in RSS_FEEDS:
        console.print(f"[dim]🔍 Leyendo {feed_config['name']}...[/dim]", end="")
        jobs = process_feed(feed_config, seen_ids)
        all_jobs.extend(jobs)
        status = f"[green]{len(jobs)} nuevos[/green]" if jobs else "[dim]0[/dim]"
        console.print(f" {status}")

    console.print()
    print_results(all_jobs, console)
    saved = save_jobs_to_csv(all_jobs, OUTPUT_CSV)
    console.print()
    print_summary(all_jobs, saved, console)


if __name__ == "__main__":
    main()