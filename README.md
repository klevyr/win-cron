# Crontab para Window$

Reemplaza el programador de tareas de window$, este requiere elevaciones y no es viable cuando las politicas de cambio de contrasenia obliga a cambiarla periodicamente.

Para linux puedes incluir en la lista de tareas de crontab que viene por defecto. El archivo `contrab.txt` es compatible con linux.

## Crontab como Servicio

- Inicializacion, abriendo una ventana de comandos con permisos de administrador.

```bash
python CrontabService.py install
```

- Iniciar el servicio

```bash
python CrontabService.py start
```

- Detener el servicio

```bash
python CrontabService.py stop
```

- Eliminar el servicio

```bash
python CrontabService.py remove
```

**IMPORTANTE!** Las tareas programadas tendran los mismos permisos, debe asegurarse de que la configuracion del servicio se encuentre limitado.

## Creditos

**winCron**, https://github.com/micromys/winCron
