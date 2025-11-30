import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

load_dotenv()

class SpotifyManager:
    def __init__(self) -> None:
        scope: str = "user-library-read playlist-modify-public playlist-modify-private"
        self.sp: spotipy.Spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
        self.user_id: str = self.sp.current_user()['id']

    # ... [MANTENER MÉTODOS ANTERIORES: search_top_tracks_..., search_generic] ...
    # Copia aquí los métodos de búsqueda anteriores (artist, genre, decade, generic)
    # por brevedad no los repito, pero NO los borres.

    def search_top_tracks_artist(self, artist_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        results = self.sp.search(q='artist:' + artist_name, type='artist')
        items = results['artists']['items']
        if len(items) > 0:
            artist_id = items[0]['id']
            top_tracks = self.sp.artist_top_tracks(artist_id)
            return self._parse_tracks(top_tracks['tracks'][:limit])
        return []

    def search_top_tracks_genre(self, genre: str, limit: int = 10) -> List[Dict[str, Any]]:
        query = f'genre:{genre}'
        results = self.sp.search(q=query, type='track', limit=limit)
        return self._parse_tracks(results['tracks']['items'])

    def search_top_tracks_decade(self, year_start: int, year_end: int, limit: int = 10) -> List[Dict[str, Any]]:
        query = f'year:{year_start}-{year_end}'
        results = self.sp.search(q=query, type='track', limit=limit)
        return self._parse_tracks(results['tracks']['items'])

    def search_generic(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        results = self.sp.search(q=query, type='track', limit=limit)
        return self._parse_tracks(results['tracks']['items'])

    # --- NUEVOS MÉTODOS PARA MERGE / PLAYLISTS ---

    def search_playlists(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Busca playlists públicas."""
        results = self.sp.search(q=query, type='playlist', limit=limit)
        # Parseamos un poco distinto porque es info de playlist, no tracks
        return [{'name': p['name'], 'id': p['id'], 'owner': p['owner']['display_name'], 'total': p['tracks']['total']} 
                for p in results['playlists']['items']]

    def get_playlist_tracks_all(self, playlist_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene TODAS las canciones de una playlist (maneja paginación).
        Útil para importar playlists grandes.
        """
        results = self.sp.playlist_items(playlist_id)
        tracks_data = results['items']
        
        # Paginación: mientras haya una página siguiente ('next'), seguimos buscando
        while results['next']:
            results = self.sp.next(results)
            tracks_data.extend(results['items'])
            
        return self._parse_playlist_items(tracks_data)

    def get_user_playlists(self) -> List[Dict[str, Any]]:
        playlists = self.sp.current_user_playlists()
        return [{'name': p['name'], 'id': p['id'], 'total': p['tracks']['total']} for p in playlists['items']]

    def create_playlist(self, name: str, description: str = "Creada con Python Script") -> str:
        playlist = self.sp.user_playlist_create(self.user_id, name, public=True, description=description)
        return playlist['id']

    def add_tracks_to_playlist(self, playlist_id: str, track_uris: List[str]) -> None:
        if not track_uris: return
        chunk_size = 100
        for i in range(0, len(track_uris), chunk_size):
            chunk = track_uris[i : i + chunk_size]
            self.sp.playlist_add_items(playlist_id, chunk)

    # --- PARSERS ---

    def _parse_tracks(self, tracks_data: List[Any]) -> List[Dict[str, Any]]:
        """Parser para resultados de búsqueda (Search API)."""
        clean_tracks = []
        for track in tracks_data:
            if track and track.get('artists') and track.get('album'):
                clean_tracks.append({
                    'name': track['name'],
                    'artist': track['artists'][0]['name'],
                    'album': track['album']['name'],
                    'uri': track['uri']
                })
        return clean_tracks

    def _parse_playlist_items(self, items_data: List[Any]) -> List[Dict[str, Any]]:
        """
        Parser específico para items de una playlist.
        La estructura es diferente: item['track'] contiene la info.
        """
        clean_tracks = []
        for item in items_data:
            # A veces hay tracks nulos o episodios de podcast sin URI correcto
            track = item.get('track')
            if track and track.get('id') and track.get('artists'):
                clean_tracks.append({
                    'name': track['name'],
                    'artist': track['artists'][0]['name'],
                    'album': track['album']['name'],
                    'uri': track['uri']
                })
        return clean_tracks

    def search_tracks_by_batch_queries(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        Recibe una lista de strings (ej: ['Queen - Bohemian', 'Despacito']).
        Busca cada una y devuelve el MEJOR resultado (Top 1) de cada búsqueda.
        """
        found_tracks = []
        not_found = []

        print(f"🔄 Procesando {len(queries)} líneas del archivo...")

        for i, query in enumerate(queries):
            # Limpiamos espacios extra
            q = query.strip()
            if not q: continue

            try:
                # Buscamos solo 1 resultado (el más probable)
                results = self.sp.search(q=q, type='track', limit=1)
                items = results['tracks']['items']
                
                if items:
                    track = self._parse_tracks(items)[0]
                    found_tracks.append(track)
                    print(f"   [OK] {q[:20]}... -> {track['name']} ({track['artist']})")
                else:
                    not_found.append(q)
                    print(f"   [X]  No encontrado: {q}")
                
                # Pequeña pausa para no saturar la API si la lista es gigante
                # (Spotify tiene rate limits)
                if i % 10 == 0:
                    time.sleep(0.5)

            except Exception as e:
                print(f"   [Error] falló '{q}': {e}")

        if not_found:
            print(f"\n⚠ No se encontraron {len(not_found)} canciones: {not_found}")
            
        return found_tracks
