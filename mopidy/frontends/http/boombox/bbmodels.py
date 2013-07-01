from mopidy.models import ImmutableObject
import bbconst
import json
class bbTrack():
    """
    A tracklist track. Wraps a regular track and it's tracklist ID.

    The use of :class:`TlTrack` allows the same track to appear multiple times
    in the tracklist.

    This class also accepts it's parameters as positional arguments. Both
    arguments must be provided, and they must appear in the order they are
    listed here.

    This class also supports iteration, so your extract its values like this::

        (tlid, track) = tl_track

    :param tlid: tracklist ID
    :type tlid: int
    :param track: the track
    :type track: :class:`Track`
    """

    #: The tracklist that it gets in the "real playlist"
    tlid = None

    #: The bb_tracklist ID. Read-only.
    bbid = 0

    #: The track. Read-only.
    track = None

    #: Number of votes for the track
    votes = None

    #: msg of whom added the track
    msg = None
    
    #: name of whom added the track
    user = None
    
    cover_url = None

    def __init__(self, mtrack , mid, mmsg="", mname="" ):
        self.track = mtrack
        self.votes = bbconst.INIT_VOTES
        self.user = mname
        self.msg = mmsg
        self.bbid = mid
        self.cover_url=""
      
    def __iter__(self):
        return iter([self.bbid, self.track])
        
        

    def serialize(self):
        data = {}
        data['__model__'] = self.__class__.__name__
        for key in self.__dict__.keys():
            public_key = key.lstrip('_')
            value = self.__dict__[key]
            if isinstance(value, (set, frozenset, list, tuple)):
                value = [o.serialize() for o in value]
            elif isinstance(value, ImmutableObject):
                value = value.serialize()
            if value:
                data[public_key] = value
        return data


class ModelJSONEncoder(json.JSONEncoder):
        """
        Automatically serialize Mopidy models to JSON.

        Usage::

            >>> import json
            >>> json.dumps({'a_track': Track(name='name')}, cls=ModelJSONEncoder)
            '{"a_track": {"__model__": "Track", "name": "name"}}'

        """
        def default(self, obj):
            if isinstance(obj, bbTrack):
                return obj.serialize()
            return json.JSONEncoder.default(self, obj)