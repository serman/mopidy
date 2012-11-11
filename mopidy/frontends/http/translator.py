import os
import re

from mopidy import settings
from mopidy.frontends.mpd import protocol
from mopidy.models import CpTrack
from mopidy.utils.path import mtime as get_mtime, uri_to_path, split_path


def track_to_dict_format(track, position=None):
    """
    Format track for output to a dict that is easily encoded into json.

    :param track: the track
    :type track: :class:`mopidy.models.Track` or :class:`mopidy.models.CpTrack`
    :param position: track's position in playlist
    :type position: integer
    """
    if isinstance(track, CpTrack):
        (cpid, track) = track
    else:
        (cpid, track) = (None, track)
    result = [
        ('file', track.uri or ''),
        ('Time', track.length and (track.length // 1000) or 0),
        ('Artist', artists_to_dict_format(track.artists)),
        ('Title', track.name or ''),
        ('Album', track.album and track.album.name or ''),
        ('Date', track.date or ''),
    ]
    if track.album is not None and track.album.num_tracks != 0:
        result.append(('Track', '%d/%d' % (
            track.track_no, track.album.num_tracks)))
    else:
        result.append(('Track', track.track_no))
    if track.album is not None and track.album.artists:
        artists = artists_to_dict_format(track.album.artists)
        result.append(('AlbumArtist', artists))
    if position is not None and cpid is not None:
        result.append(('Pos', position))
        result.append(('Id', cpid))
    if track.album is not None and track.album.musicbrainz_id is not None:
        result.append(('MUSICBRAINZ_ALBUMID', track.album.musicbrainz_id))
    # FIXME don't use first and best artist?
    # FIXME don't duplicate following code?
    if track.album is not None and track.album.artists:
        artists = filter(
            lambda a: a.musicbrainz_id is not None, track.album.artists)
        if artists:
            result.append(
                ('MUSICBRAINZ_ALBUMARTISTID', artists[0].musicbrainz_id))
    if track.artists:
        artists = filter(lambda a: a.musicbrainz_id is not None, track.artists)
        if artists:
            result.append(('MUSICBRAINZ_ARTISTID', artists[0].musicbrainz_id))
    if track.musicbrainz_id is not None:
        result.append(('MUSICBRAINZ_TRACKID', track.musicbrainz_id))
    
    return dict(result)




def artists_to_dict_format(artists):
    """
    Format track artists for output to MPD client.

    :param artists: the artists
    :type track: array of :class:`mopidy.models.Artist`
    :rtype: string
    """
    artists = list(artists)
    artists.sort(key=lambda a: a.name)
    return u', '.join([a.name for a in artists if a.name])


def tracks_to_dict_format(tracks, start=0, end=None):
    """
    Format list of tracks for output to MPD client.

    Optionally limit output to the slice ``[start:end]`` of the list.

    :param tracks: the tracks
    :type tracks: list of :class:`mopidy.models.Track` or
        :class:`mopidy.models.CpTrack`
    :param start: position of first track to include in output
    :type start: int (positive or negative)
    :param end: position after last track to include in output
    :type end: int (positive or negative) or :class:`None` for end of list
    :rtype: list of lists of two-tuples
    """
    if end is None:
        end = len(tracks)
    tracks = tracks[start:end]
    positions = range(start, end)
    assert len(tracks) == len(positions)
    result = []
    for track, position in zip(tracks, positions):
        result.append(track_to_dict_format(track, position))
    return result


def playlist_to_dict_format(playlist, *args, **kwargs):
    """
    Format playlist for output to MPD client.

    Arguments as for :func:`tracks_to_mpd_format`, except the first one.
    """
    return tracks_to_dict_format(playlist.tracks, *args, **kwargs)


