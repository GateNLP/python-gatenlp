from gatenlp.changelog import ChangeLog


class AnnotationGraph:
    def __init__(self, name: str = "", changelog: ChangeLog = None, owner_set: "AnnotationSet" = None):
        """
        Create a new annotation graph.
        NOTE: an new annotation graph should never be created separately but be constructed using the
        AnnotationSet.get_graph(name) method.
        :param name: the name of the annotation set. This is only really needed if the changelog is used.
        :param changelog: if a changelog is used, then all changes to the set and its annotations are logged
        :param owner_set: the owning annotation set
        """
        self.gatenlp_type = "AnnotationGraph"
        self.changelog = changelog
        self.name = name
        self._owner_set = owner_set

        self._edges = {}
        self._is_immutable = False
        self._max_edgeid = 0
