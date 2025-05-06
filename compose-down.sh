#!/bin/bash

echo "🛑 Arresto e smontaggio dei container con podman-compose..."

# Verifica se 'podman-compose' è disponibile
if ! command -v podman-compose &> /dev/null
then
    echo "❌ 'podman-compose' non è installato o non è nel PATH."
    echo "   Esegui: pip3 install --user podman-compose"
    exit 1
fi

# Ferma e rimuove i container definiti nel compose
podman-compose down

echo ""
echo "🔍 Container ancora attivi:"
podman ps -a

echo ""
echo "📦 Immagini disponibili:"
podman images

echo ""
echo "🗃️ Volumi persistenti:"
podman volume ls

echo ""
read -p "❓ Vuoi eliminare *tutti* i container fermi, le immagini e i volumi? Digita 'delete' per confermare: " confirm

if [[ "$confirm" == "delete" ]]; then
    echo ""
    echo "🔥 Eliminazione in corso..."

    echo "🔻 Rimozione container fermi..."
    podman container prune -f

    echo "🔻 Rimozione immagini non usate..."
    podman image prune -a -f

    echo "🔻 Rimozione volumi non usati..."
    podman volume prune -f

    echo "✅ Tutto è stato cancellato!"
else
    echo "❎ Nessuna eliminazione effettuata. Risorse ancora disponibili."
fi

echo ""
echo "🔍 Container ancora attivi:"
podman ps -a

echo ""
echo "📦 Immagini disponibili:"
podman images

echo ""
echo "🗃️ Volumi persistenti:"
podman volume ls