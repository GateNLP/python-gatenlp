"""
An Edge for an AnnotationGraph: this describes a directed or undirected edge between
to nodes in an AnnotationGraph, where the nodes are always annotations.
"""
from typing import List, Union, Dict, Set
from gatenlp.feature_bearer import FeatureBearer
from gatenlp.changelog import ChangeLog


class Edge(FeatureBearer):

    # We use slots to avoid the dict and save memory if we have a large number of annotations
    __slots__ = ('type', 'from_node', 'to_node', 'features', 'id')

    # Instead of storing owner setname and owner graphname, it should be less effort to
    # just store the owner graph instance in a transient field
    def __init__(self, from_node: int, to_node: int, edge_type: str, edge_id: int,
                 changelog=None, features=None, owner=None):
        """
        Create a new edge instance. NOTE: this should almost never be done directly
        and instead the method AnnotationGraph.add should be used!
        Once an edge has been created, the from_node, to_node, type and id fields must not
        be changed!
        :param from_node: the starting point of the edge
        :param to_node: the end point of the edge
        :param edge_type: the type/label of the edge
        :param edge_id: the id of the edge
        :param changelog: a ChangeLog instance to track changes or None to not track changes
        :param features: an initial collection of features
        """
        super().__init__(features)
        self.gatenlp_type = "Edge"
        self.changelog = changelog
        self.type = edge_type
        self.from_node = from_node
        self.to_node = to_node
        self.id = edge_id
        self._owner = owner

    def _log_feature_change(self, command: str, feature: str = None, value=None) -> None:
        if self.changelog is None:
            return
        ch = {
            "command": command,
            # TODO:!!!!
            # "set": self.owner.,  # access the set in the graph, then the name of the set
            # "graph": self.owner.name # access the graph, then the name of the graph
            "id": self.id}
        if feature is not None:
            ch["feature"] = feature
        if value is not None:
            ch["value"] = value
        self.changelog.append(ch)

    def __eq__(self, other) -> bool:
        """
        Equality of edges is only based on the edge ID! This means you should never compare annotations
        from different sets directly!
        :param other: the object to compare with
        :return:
        """
        if not isinstance(other, Edge):
            return False
        if self.owner != other.owner:
            return False
        if self.id != other.id:
            return False
        else:
            return True

    def __hash__(self):
        """
        The hash only depends on the annotation ID! This means you should never add annotations from different sets
        directly to a map or other collection that depends on the hash.
        :return:
        """
        return hash(self.id)

    def __repr__(self) -> str:
        """
        String representation of the edge.
        :return: string representation
        """
        return "Edge({},{},{},id={},features={})".format(self.from_node, self.to_node, self.type, self.id, self.features)

    def _json_repr(self, **kwargs) -> Dict:
        return {
            "from_node": self.from_node,
            "to_node": self.to_node,
            "type": self.type,
            "id": self.id,
            "features": self.features,
            "gatenlp_type": self.gatenlp_type
        }

    @staticmethod
    def _from_json_map(jsonmap, **kwargs) -> "Edge":
        edge = Edge(jsonmap.get("from_node"), jsonmap.get("to_node"), jsonmap.get("type"), jsonmap.get("id"),
                   features=jsonmap.get("features"))
        return edge

    def __setattr__(self, key, value):
        """
        Prevent from_node, to_node, type and edge id from getting overridden, once they have been
        set.
        :param key: attribute to set
        :param value: value to set attribute to
        :return:
        """
        if key == "from_node" or key == "to_node" or key == "type" or key == "id":
            if self.__dict__.get(key, None) is None:
                super().__setattr__(key, value)
            else:
                raise Exception("Edge attributes cannot get changed after being set")
        else:
            super().__setattr__(key, value)

