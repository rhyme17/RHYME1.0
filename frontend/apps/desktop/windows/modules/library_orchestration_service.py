class LibraryOrchestrationService:
    @staticmethod
    def normalize_library_songs(songs, normalize_text_callable):
        normalized_songs = songs or []
        normalized_by_id = {}
        updated_count = 0

        for song in normalized_songs:
            original_title = song.get("title", "")
            original_artist = song.get("artist", "")
            original_album = song.get("album", "")

            normalized_title = normalize_text_callable(original_title, "未知歌曲")
            normalized_artist = normalize_text_callable(original_artist, "未知艺术家")
            normalized_album = normalize_text_callable(original_album, "未知专辑")

            if (
                normalized_title != original_title
                or normalized_artist != original_artist
                or normalized_album != original_album
            ):
                song["title"] = normalized_title
                song["artist"] = normalized_artist
                song["album"] = normalized_album
                updated_count += 1

            normalized_by_id[song.get("id")] = {
                "title": song.get("title", ""),
                "artist": song.get("artist", "未知艺术家"),
                "album": song.get("album", ""),
            }

        return updated_count, normalized_by_id

    @staticmethod
    def sync_playlists_song_metadata(playlists, normalized_by_id):
        updated_count = 0
        for songs in (playlists or {}).values():
            for song in songs:
                song_id = song.get("id")
                normalized = normalized_by_id.get(song_id)
                if not normalized:
                    continue
                if (
                    song.get("title") != normalized["title"]
                    or song.get("artist") != normalized["artist"]
                    or song.get("album") != normalized["album"]
                ):
                    song["title"] = normalized["title"]
                    song["artist"] = normalized["artist"]
                    song["album"] = normalized["album"]
                    updated_count += 1
        return updated_count

    @staticmethod
    def sync_current_song_metadata(current_song, normalized_by_id):
        if not current_song:
            return None
        normalized = normalized_by_id.get(current_song.get("id"))
        if not normalized:
            return None
        current_song["title"] = normalized["title"]
        current_song["artist"] = normalized["artist"]
        return normalized

