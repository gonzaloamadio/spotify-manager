"""
=== How to merge 2 playlists ===

- Eliges Opción 5 (Importar).
- Buscas, por ejemplo, "Top 50 Global" (Pública) o eliges tu playlist "Rock Viejo".
- El script descarga las canciones.
- Te preguntará qué quieres seleccionar.
- Para un Merge Completo: Escribes all.
Para un Merge Parcial: Escribes 1..10, 50..60.
- Las canciones pasan a la Lista Temporal.
- Eliges Opción 7 (Guardar) y las vuelcas en la playlist destino.

"""
from spotify_helper import SpotifyManager
from typing import List, Dict, Any, Set
import sys

# ... [MANTENER FUNCIONES: print_tracks, get_user_limit, parse_selection_string, select_tracks_logic] ...
# (Copia las funciones de UI del paso anterior aquí)

def print_tracks(tracks: List[Dict[str, Any]]) -> None:
    if not tracks:
        print("No se encontraron canciones.")
        return
    print(f"\nResultados encontrados ({len(tracks)}):")
    print(f"{'IDX':<4} | {'ARTISTA':<20} | {'CANCIÓN':<30}")
    print("-" * 60)
    for i, track in enumerate(tracks):
        artist = (track['artist'][:18] + '..') if len(track['artist']) > 18 else track['artist']
        song = (track['name'][:28] + '..') if len(track['name']) > 28 else track['name']
        print(f"{i+1:<4} | {artist:<20} | {song:<30}")

def get_user_limit() -> int:
    user_input = input("¿Cuántos resultados quieres? (Enter para 10): ")
    if user_input.strip() == "": return 10
    try:
        limit = int(user_input)
        return limit if limit > 0 else 10
    except ValueError:
        return 10

def parse_selection_string(selection_str: str) -> List[int]:
    selected_indices: Set[int] = set()
    parts = selection_str.split(',')
    for part in parts:
        part = part.strip()
        if '..' in part:
            try:
                bounds = part.split('..')
                if len(bounds) == 2:
                    start = int(bounds[0])
                    end = int(bounds[1])
                    for i in range(start, end + 1):
                        selected_indices.add(i - 1)
            except ValueError: pass
        elif part.isdigit():
            selected_indices.add(int(part) - 1)
    return sorted(list(selected_indices))

def select_tracks_logic(found_tracks: List[Dict[str, Any]], staging_list: List[Dict[str, Any]]) -> None:
    print_tracks(found_tracks)
    if not found_tracks: return
    print("\nOpciones: 'all' (todas), '0' (cancelar), rangos (ej: 1..25, 27)")
    selection = input(">> Selección: ")
    if selection == '0': return
    
    selected_indices = []
    if selection.lower() == 'all':
        selected_indices = range(len(found_tracks))
    else:
        selected_indices = parse_selection_string(selection)

    count = 0
    for idx in selected_indices:
        if 0 <= idx < len(found_tracks):
            track = found_tracks[idx]
            if track not in staging_list:
                staging_list.append(track)
                count += 1
    print(f"✅ Se agregaron {count} canciones a la Lista Temporal.")

# --- MENÚ PRINCIPAL ACTUALIZADO ---

def print_menu() -> None:
    print("\n--- SPOTIFY MANAGER ---")
    print("1. Buscar Top canciones de un ARTISTA")
    print("2. Buscar Top canciones de un GÉNERO")
    print("3. Buscar Top canciones de una DÉCADA")
    print("4. Búsqueda LIBRE (Generic Query)")
    print("5. IMPORTAR / MERGE (Desde otra Playlist)") # <--- NUEVO
    print("6. Ver mi 'Lista Temporal' (Staging Area)")
    print("7. Guardar 'Lista Temporal' en una Playlist")
    print("8. Ver mis Playlists")
    print("9. Salir")
    print("-" * 25)

def main() -> None:
    try:
        manager = SpotifyManager()
        print(f"Conectado como usuario: {manager.user_id}")
    except Exception as e:
        print("Error conectando con Spotify. Revisa tu archivo .env")
        return

    staging_area: List[Dict[str, Any]] = []

    while True:
        print_menu()
        choice = input("Elige una opción: ")

        if choice == '1':
            artist = input("Nombre del artista: ")
            limit = get_user_limit()
            tracks = manager.search_top_tracks_artist(artist, limit=limit)
            select_tracks_logic(tracks, staging_area)

        elif choice == '2':
            genre = input("Género (ej: rock, pop): ")
            limit = get_user_limit()
            tracks = manager.search_top_tracks_genre(genre, limit=limit)
            select_tracks_logic(tracks, staging_area)

        elif choice == '3':
            decade = input("Año de inicio: ")
            try:
                start = int(decade); end = start + 9
                limit = get_user_limit()
                tracks = manager.search_top_tracks_decade(start, end, limit=limit)
                select_tracks_logic(tracks, staging_area)
            except: print("Año inválido.")

        elif choice == '4':
            query = input("Búsqueda (ej: artist:'Gustavo Cerati' NOT track:live NOT track:remix): ")
            limit = get_user_limit()
            tracks = manager.search_generic(query, limit=limit)
            select_tracks_logic(tracks, staging_area)

        # --- NUEVA LÓGICA DE MERGE ---
        elif choice == '5':
            print("\n--- IMPORTAR CANCIONES ---")
            print("1. Buscar una Playlist PÚBLICA")
            print("2. Importar desde MIS Playlists")
            sub = input(">> ")
            
            selected_playlist_id = None
            
            if sub == '1':
                q = input("Nombre de la playlist a buscar: ")
                results = manager.search_playlists(q)
                if not results:
                    print("No se encontraron playlists.")
                    continue
                
                print(f"\nPlaylists encontradas:")
                for i, p in enumerate(results):
                    print(f"{i+1}. {p['name']} (por {p['owner']} - {p['total']} canciones)")
                
                try:
                    idx = int(input("Selecciona #: ")) - 1
                    if 0 <= idx < len(results):
                        selected_playlist_id = results[idx]['id']
                except: pass

            elif sub == '2':
                results = manager.get_user_playlists()
                print("\nMis Playlists:")
                for i, p in enumerate(results):
                    print(f"{i+1}. {p['name']} ({p['total']} canciones)")
                try:
                    idx = int(input("Selecciona #: ")) - 1
                    if 0 <= idx < len(results):
                        selected_playlist_id = results[idx]['id']
                except: pass

            if selected_playlist_id:
                print("⏳ Cargando canciones (esto puede tardar si son muchas)...")
                # Usamos la función que trae TODO (sin límite de 10)
                tracks = manager.get_playlist_tracks_all(selected_playlist_id)
                print(f"Playlist cargada: {len(tracks)} canciones encontradas.")
                
                # Reutilizamos la lógica de selección. 
                # Si el usuario quiere hacer merge total, solo escribe 'all'
                select_tracks_logic(tracks, staging_area)

        elif choice == '6':
            print(f"\n--- LISTA TEMPORAL ({len(staging_area)}) ---")
            print_tracks(staging_area)
            if staging_area and input("¿Limpiar? (s/n): ").lower() == 's': staging_area.clear()

        elif choice == '7':
            if not staging_area:
                print("Lista vacía.")
                continue
            print("1. Nueva Playlist | 2. Existente")
            sub = input(">> ")
            uris = [t['uri'] for t in staging_area]
            if sub == '1':
                name = input("Nombre: ")
                pid = manager.create_playlist(name)
                manager.add_tracks_to_playlist(pid, uris)
                print("✅ Guardado.")
                staging_area.clear()
            elif sub == '2':
                pls = manager.get_user_playlists()
                for i, p in enumerate(pls): print(f"{i+1}. {p['name']}")
                try:
                    pid = pls[int(input("#: "))-1]['id']
                    manager.add_tracks_to_playlist(pid, uris)
                    print("✅ Guardado.")
                    staging_area.clear()
                except: pass

        elif choice == '8':
            pls = manager.get_user_playlists()
            print("\n--- MIS PLAYLISTS ---")
            for p in pls: print(f"- {p['name']} ({p.get('total',0)} songs)")

        elif choice == '9':
            sys.exit()

if __name__ == "__main__":
    main()
