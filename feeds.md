# RSS Feeds de Trabajo Remoto

Lista de feeds que podés usar en `job_watcher.py`.

## Ya incluidos en el script

| Nombre | URL | Categoría |
|--------|-----|-----------|
| We Work Remotely – Programming | https://weworkremotely.com/categories/remote-programming-jobs.rss | Dev |
| We Work Remotely – DevOps | https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss | DevOps |
| Remotive | https://remotive.com/rss/remote-jobs | General |
| Remote OK | https://remoteok.com/remote-jobs.rss | General |
| Stack Overflow Jobs | https://stackoverflow.com/jobs/feed?r=true | Dev |

## Feeds adicionales para agregar

### Por categoría de trabajo

| Nombre | URL |
|--------|-----|
| We Work Remotely – Design | https://weworkremotely.com/categories/remote-design-jobs.rss |
| We Work Remotely – Customer Support | https://weworkremotely.com/categories/remote-customer-support-jobs.rss |
| Remotive – QA | https://remotive.com/rss/remote-jobs/qa |
| Remotive – Software Dev | https://remotive.com/rss/remote-jobs/software-dev |
| Remotive – DevOps | https://remotive.com/rss/remote-jobs/devops |

### Boards populares

| Nombre | URL |
|--------|-----|
| Jobicy | https://jobicy.com/?feed=job_feed |
| EuropeRemotely | https://europeremotely.com/feed |
| Remote.co | https://remote.co/feed/ |

### Por tecnología (LinkedIn búsquedas via RSS — opcional)
LinkedIn ya no soporta RSS nativo, pero existen herramientas como
RSS.app o Feedburner que pueden convertir búsquedas en feeds.

## Cómo agregar un feed al script

Abrí `job_watcher.py` y agregá un dict a la lista `RSS_FEEDS`:

```python
RSS_FEEDS = [
    # ... feeds existentes ...
    {
        "name": "Mi Feed Nuevo",
        "url": "https://ejemplo.com/jobs.rss",
    },
]
```

## Cómo crear un feed personalizado de LinkedIn (workaround)

1. Hacé una búsqueda en LinkedIn Jobs con los filtros que querés
2. Copiá la URL de resultados
3. Usá https://rss.app para convertirla en un RSS feed
4. Agregá la URL del feed generado a `RSS_FEEDS`
