# Build de Producao (Windows)

## Pre-requisitos
- Python 3.11+ instalado e no `PATH`.
- PowerShell.

## Gerar executavel
No raiz do projeto:

```powershell
.\scripts\build_windows.ps1
```

Saida principal:
- `dist\Alexandria\Alexandria.exe`

## Opcoes uteis
- Sem reinstalar dependencias:

```powershell
.\scripts\build_windows.ps1 -NoInstall
```

- Sem limpar `build/` e `dist/` antes:

```powershell
.\scripts\build_windows.ps1 -NoClean
```

## O que vai no pacote de producao
- `assets` filtrado para arquivos de runtime (imagens, mapas, fontes, audio).
- `code/circuitos` (`.json`) e `code/ltspice` (`.asc`, `.net`) para dados iniciais.
- Icone do executavel: `assets/images/icon/game_icon.ico`.

## Dados gravaveis em runtime
No executavel, os arquivos de circuito/netlist gravaveis sao salvos em:

`%LOCALAPPDATA%\Alexandria\code\circuitos`
`%LOCALAPPDATA%\Alexandria\code\ltspice`

Na primeira execucao, arquivos padrao sao copiados automaticamente do pacote.
