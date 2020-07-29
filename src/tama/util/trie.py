from itertools import repeat
from collections import deque
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Deque


@dataclass
class TrieNode:
    character: str
    terminator: bool = False
    members: Dict[str, "TrieNode"] = field(default_factory=dict)


class Trie:
    root: TrieNode

    def __init__(self):
        self.root = TrieNode("")

    def add(self, item: str):
        father = self.root
        for c in item[:-1]:
            node = father.members.get(c)
            if not node:
                node = father.members[c] = TrieNode(character=c)
            father = node

        if not (node := father.members.get(item[-1])):
            father.members[item[-1]] = TrieNode(
                character=item[-1], terminator=True
            )
        else:
            node.terminator = True

    def search(self, string: str) -> List[str]:
        match = self.root
        # Check if string is not empty
        if len(string) == 0:
            raise ValueError

        # Check if trie is not empty
        if len(match.members) == 0:
            return []

        # Iterate over the match string
        try:
            it = iter(string)
            while c := next(it):
                match = match.members.get(c)
                if not match:
                    # If we abort before StopIteration, no matches were found
                    return []
        except StopIteration:
            pass

        if match.terminator:
            if len(match.members) == 0:
                # We have an exact match
                return [string]
            else:
                # We have an exact match + additional matches
                matches = [string]
        else:
            # We may have matches
            matches = []

        # Iterate
        nodes: Deque[Tuple[str, TrieNode]] = deque()
        nodes.extend(zip(repeat(string), match.members.values()))
        try:
            while nx := nodes.popleft():
                prefix, n = nx
                current_str = prefix + n.character
                if n.terminator:
                    matches.append(current_str)
                nodes.extend(zip(repeat(current_str), n.members.values()))
        except IndexError:
            return matches
