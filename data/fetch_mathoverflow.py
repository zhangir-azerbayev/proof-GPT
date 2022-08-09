from dataclasses import dataclass, field, fields
from functools import lru_cache
from xml.etree import ElementTree
from datetime import datetime
from enum import Enum
import typing
from typing import List, Optional, Union
import os.path
from itertools import groupby
import dataclasses

"""
Author: E.W.Ayers

This code takes a dump of math overflow XML and produces
a structured set of questions with answers.

1. Get mathoverflow.net.7z file
2. Extract this to `DATA_DIR = 'data/mathoverflow.net'`
3. Run `questions()` and run it to get a dictionary of mathoverflow questions.
   Each question has an `Answers` field that contains a list of answers for the given q.
"""

# source: https://meta.stackexchange.com/questions/2677/database-schema-documentation-for-the-public-data-dump-and-sede
class PostType(Enum):
    Question = 1
    Answer = 2
    OrphanedTagWiki = 3
    TagWikiExcerpt = 4
    TagWiki = 5
    ModeratorNomination = 6
    WikiPlaceholder = 7
    PrivilegeWiki = 8

def is_optional(field):
    return typing.get_origin(field) is Union and type(None) in typing.get_args(field)

def fromXML(cls, element):
    out = {}
    for field in fields(cls):
        field_key = field.name
        field_type = field.type
        f = field.metadata.get('from_xml')
        if f == 'skip':
            continue
        attr_key = f['key'] if (f is not None and f['key'] is not None) else field_key
        v = element.attrib.get(attr_key)
        if v is None:
            if field.default is not dataclasses.MISSING:
                out[field_key] = field.default
            elif field.default_factory is not dataclasses.MISSING:
                out[field_key] = field.default_factory()  # type: ignore
            elif is_optional(field_type):
                out[field_key] = None
            else:
                raise Exception(f"Missing field {attr_key}")
            continue
        if is_optional(field_type):
            field_type = typing.get_args(field_type)[0]
        if f is not None and f['fn'] is not None:
            out[field_key] = f['fn'](v)
        elif field_type is int:
            out[field_key] = int(v)
        elif field_type is str:
            out[field_key] = str(v)
        elif field_type is datetime:
            out[field_key] = datetime.fromisoformat(v)
        else:
            raise Exception(f"Don't know how to decode {field_type}")
    return cls(**out)

def use(fn, key=None):
    return field(metadata={'from_xml': {'fn': fn, 'key': key}})

def skip(default):
    return field(default=default, metadata={'from_xml': 'skip'})

def iter_rows(path):
    for [_, element] in ElementTree.iterparse(path, events = ['start']):
        if (element.tag == 'row'):
            yield element

DATA_DIR = 'data/mathoverflow.net'

@dataclass
class Comment:
    Id: int
    PostId: int
    Score: int
    Text: str
    CreationDate: datetime
    UserId: Optional[int]

@lru_cache()
def comments():
    path = os.path.join(DATA_DIR, 'Comments.xml')
    out = {}
    for element in iter_rows(path):
        x : Comment = fromXML(Comment, element)
        out[x.Id] = x
    print(f"Processed {len(out)} comments.")
    return out

@dataclass
class Post:
    Id: int
    CreationDate: datetime
    DeletionDate: Optional[datetime]
    Score: int
    Body: str # in html; need to parse out?
    Title: Optional[str]
    OwnerUserId: Optional[int]
    ViewCount: Optional[int]
    AcceptedAnswerId: Optional[int]
    ParentId: Optional[int]
    PostType: "PostType" = use(lambda x: PostType(int(x)), 'PostTypeId')
    Comments: List[Comment] = skip(None)
    Answers: Optional[List["Post"]] = skip(None)
    Tags: str = field(default="")

@lru_cache()
def questions():
    path = os.path.join(DATA_DIR, 'Posts.xml')
    cs = {}
    for k, c in groupby(comments().values(), lambda c: c.PostId):
        x = list(c)
        x.sort(key =  lambda x: -x.Score)
        cs[k] = x
    qs = {}
    answers = {}
    for element in iter_rows(path):
        post = fromXML(Post, element)
        post.Comments = cs.get(post.Id, [])
        if (post.PostType is PostType.Question):
            post.Answers = []
            qs[post.Id] = post
        elif (post.PostType is PostType.Answer):
            answers[post.Id] = post
    for qk, aa in groupby(answers.values(), lambda a: a.ParentId):
        x = list(aa)
        x.sort(key = lambda x: -x.Score)
        qs[qk].Answers = x
    print(f"Processed {len(qs)} questions with {len(answers)} answers.")
    return qs

if __name__ == '__main__':
    qs = questions()
    print(f"There are {len(questions())} questions")
