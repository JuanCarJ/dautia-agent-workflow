# Instalacion en Windows con WSL

El entorno soportado es WSL2. Guarda los clones dentro del filesystem Linux
(`~/DautIA`), no en `/mnt/c`, para conservar permisos y rendimiento.

## 1. Preparar WSL

Instala Ubuntu, Git, Python 3, SSH y las herramientas que requiera cada
proyecto. Docker Desktop y Colima no forman parte del workflow; cuando un
proyecto necesite contenedores usa Docker Engine dentro de WSL.

Configura Git y autentica GitHub en WSL. Clona este repositorio privado:

```bash
mkdir -p ~/DautIA/workflow
git clone https://github.com/JuanCarJ/dautia-agent-workflow.git \
  ~/DautIA/workflow/dautia-agent-workflow
cd ~/DautIA/workflow/dautia-agent-workflow
```

## 2. Instalar para Codex y Cursor

Primero revisa lo que cambiara y despues aplica:

```bash
python3 scripts/install.py --profile wsl-shared --check
python3 scripts/install.py --profile wsl-shared --apply
python3 scripts/doctor.py --profile wsl-shared
```

Reinicia Codex y Cursor. Cursor descubre las skills instaladas en
`~/.codex/skills` y sus adaptadores de agentes en `~/.cursor/agents`.

## 3. Credenciales por host

Las credenciales nunca se copian desde el Mac. Configura una sola vez en WSL:

- sesion GitHub;
- sesion Vercel;
- sesion Supabase y una password DB por `project_ref` mediante
  `dautia-supabase`;
- SSH/Tailscale para infraestructura compartida;
- credenciales Android/Google Play cuando se necesiten.

Supabase guarda las passwords DB en
`~/.config/dautia/supabase-db-credentials.json` con permisos `0600`. En WSL no
usa el Llavero de macOS. Apple y codesign no se configuran en Windows.

## 4. Clonar productos

Clona cada producto por separado. Antes de trabajar ejecuta `git fetch` y parte
de `origin/<integration_branch>` declarado en `delivery.yaml`. Mac y Windows no
deben editar la misma rama simultaneamente.

## Actualizar el workflow

```bash
cd ~/DautIA/workflow/dautia-agent-workflow
git pull --ff-only
python3 scripts/install.py --profile wsl-shared --apply
python3 scripts/doctor.py --profile wsl-shared
```
