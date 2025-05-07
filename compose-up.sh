#!/usr/bin/env bash
set -e

echo "🔎 Verifica prerequisiti Podman/Podman-Compose…"

# 1) podman-compose installato?
if ! command -v podman-compose &>/dev/null; then
  cat <<-EOF

❌ 'podman-compose' non è installato o non è nel PATH.

📦 Per installarlo:
   pip3 install --user podman-compose

🔧 Aggiungi al tuo PATH (adatta la versione Python se serve):
   echo 'export PATH="\$HOME/Library/Python/3.9/bin:\$PATH"' >> ~/.zshrc
   source ~/.zshrc

EOF
  exit 1
fi

# 2) Podman disponibile e demone raggiungibile?
if ! podman info &>/dev/null; then
  cat <<-EOF

❌ Non riesco a connettermi al demone Podman.

🔍 Controlla le connessioni:
   podman system connection list

🔧 Se non ne hai (o vuoi ripartire):
   podman machine init
   podman machine start

EOF
  exit 1
fi

# 3) C’è una connessione Default con ReadWrite=true?
if ! podman system connection list --format=json \
    | jq -e '.[] | select(.Default==true and .ReadWrite==true)' &>/dev/null; then
  cat <<-EOF

❌ Non ho trovato una Podman machine configurata come 'Default' e 'ReadWrite'.

ℹ️ Le connessioni attuali sono:
   podman system connection list

🔧 Per crearne una di default:
   podman machine init
   podman machine start

EOF
  exit 1
fi

echo ""
read -p "❓ Digita 'delete' per eliminare lo stack precedente: " confirm

if [[ "$confirm" == "delete" ]]; then
  echo "🔄 Pulizia dei container precedenti…"
  ./compose-down.sh
else
  # OK, avviso e avvio
  echo "✅ Tutti i prerequisiti sono soddisfatti — avvio lo stack…"
  podman-compose down
  podman-compose up --build # poi avvia il resto dello stack
fi

