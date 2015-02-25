"""Classes for representing a Collection+JSON document."""
from __future__ import absolute_import, unicode_literals
import json


__version__ = '0.1.0'


def _from_dict_or_value(value, cls):
    """Converts the value from dictionary to the specified class or
    throws an error.

    Value must be either None, dictionary or an instance of cls.

    :param value dict|cls: value to convert
    :param cls type: class to convert to
    """
    if value is None or isinstance(value, cls):
        return value
    elif isinstance(value, dict):
        return cls(**value)
    raise TypeError("Invalid value '%s', "
                    "expected dict or '%s'" % (value, cls.__name__))


def _from_iterable_to_array(cls, name, iterable=None):
    """Converts an iterable to an Array of the specified type.

    :param cls type: class to build an array of.
    :param name str: attribute name
    :param iterable enumerable: the iterable to convert
    """
    if iterable is None:
        iterable = []
    return Array(cls, name, iterable)


class ComparableObject(object):

    """Abstract base class for objects implementing equality comparison.

    This class provides default __eq__ and __ne__ implementations.

    """

    def __eq__(self, other):
        """Return True if both instances are equivalent."""
        return (type(self) == type(other) and
                self.__dict__ == other.__dict__)

    def __ne__(self, other):
        """Return True if both instances are not equivalent."""
        return (type(self) != type(other) or
                self.__dict__ != other.__dict__)


class Collection(ComparableObject):

    """Object representing a Collection+JSON document."""

    @staticmethod
    def from_json(data):
        """Return a Collection instance.

        This method parses a json string into a Collection object.

        Raises `ValueError` when no valid document is provided.

        """
        try:
            data = json.loads(data)
            kwargs = data.get('collection')
            if not kwargs:
                raise ValueError
        except ValueError:
            raise ValueError('Not a valid Collection+JSON document.')

        collection = Collection(**kwargs)
        return collection

    def __init__(self, href, links=None, items=None, queries=None,
                 template=None, error=None, version='1.0'):
        self.version = version
        self.href = href

        self.error = error
        self.template = template
        self.items = items
        self.links = links
        self.queries = queries

    @property
    def error(self):
        return self.__error

    @error.setter
    def error(self, value):
        self.__error = _from_dict_or_value(value, Error)

    @property
    def template(self):
        return self.__template

    @template.setter
    def template(self, value):
        self.__template = _from_dict_or_value(value, Template)

    @property
    def items(self):
        return self.__items

    @items.setter
    def items(self, value):
        self.__items = _from_iterable_to_array(Item, "items", value)

    @property
    def links(self):
        return self.__links

    @links.setter
    def links(self, value):
        self.__links = _from_iterable_to_array(Link, "links", value)

    @property
    def queries(self):
        return self.__queries

    @queries.setter
    def queries(self, value):
        self.__queries = _from_iterable_to_array(Query, "queries", value)

    def __repr__(self):
        return "<Collection: version='%s' href='%s'>" % (
            self.version, self.href)

    def __str__(self):
        return json.dumps(self.to_dict())

    def to_dict(self):
        """Return a dictionary representing a Collection object."""
        output = {
            'collection': {
                'version': self.version,
                'href': self.href,
            }
        }
        if self.links:
            output['collection'].update(self.links.to_dict())
        if self.items:
            output['collection'].update(self.items.to_dict())
        if self.queries:
            output['collection'].update(self.queries.to_dict())
        if self.template:
            output['collection'].update(self.template.to_dict())
        if self.error:
            output['collection'].update(self.error.to_dict())
        return output


class Error(ComparableObject):

    """Object representing a Collection+JSON error object."""

    def __init__(self, code=None, message=None, title=None):
        self.code = code
        self.message = message
        self.title = title

    def __repr__(self):
        data = ''
        if self.code is not None:
            data += " code='%s'" % self.code
        if self.message is not None:
            data += " message='%s'" % self.message
        if self.title is not None:
            data += " title='%s'" % self.title
        return "<Error%s>" % data

    def to_dict(self):
        """Return a dictionary representing the Error instance."""
        output = {
            'error': {
            }
        }
        if self.code:
            output['error']['code'] = self.code
        if self.message:
            output['error']['message'] = self.message
        if self.title:
            output['error']['title'] = self.title
        return output


class Template(ComparableObject):

    """Object representing a Collection+JSON template object."""

    @staticmethod
    def from_json(data):
        """Return a template instance.

        Convenience method for parsing 'write' responses,
        which should only contain a template object.

        This method parses a json string into a Template object.

        Raises `ValueError` when no valid document is provided.

        """
        try:
            data = json.loads(data)
            kwargs = data.get('template')
            if not kwargs:
                raise ValueError
        except ValueError:
            raise ValueError('Not valid Collection+JSON template data.')

        template = Template(**kwargs)
        return template

    def __init__(self, data=None):
        self.data = data

    def __repr__(self):
        data = [str(item.name) for item in self.data]
        return "<Template: data=%s>" % data

    def __getattr__(self, name):
        return getattr(self.data, name)

    @property
    def data(self):
        return self.__data

    @data.setter
    def data(self, value):
        self.__data = _from_iterable_to_array(Data, "data", value)

    @property
    def properties(self):
        """Return a list of names that can be looked up on the template."""
        return [item.name for item in self.data]

    def to_dict(self):
        """Return a dictionary representing a Template object."""
        return {
            'template': self.data.to_dict()
        }


class Array(ComparableObject, list):

    """Object representing a Collection+JSON array."""

    def __init__(self, item_class, collection_name, items):
        self.item_class = item_class
        self.collection_name = collection_name
        super(Array, self).__init__(self._build_items(items))

    def _build_items(self, items):
        result = []
        for item in items:
            if isinstance(item, self.item_class):
                result.append(item)
            elif isinstance(item, dict):
                result.append(self.item_class(**item))
            else:
                raise ValueError("Invalid value for %s: %r" % (
                    self.item_class.__name__, item))
        return result

    def __eq__(self, other):
        """Return True if both instances are equivalent."""
        return (super(Array, self).__eq__(other) and
                list.__eq__(self, other))

    def __ne__(self, other):
        """Return True if both instances are not equivalent."""
        return (super(Array, self).__ne__(other) or
                list.__ne__(self, other))

    def __getattr__(self, name):
        results = self.find(name=name)

        if not results:
            raise AttributeError
        elif len(results) == 1:
            results = results[0]
        return results

    def _matches(self, name=None, rel=None):
        for item in self:
            item_name = getattr(item, 'name', None)
            item_rel = getattr(item, 'rel', None)

            if name is not None and item_name == name and rel is None:
                # only searching by name
                yield item
            elif rel is not None and item_rel == rel and name is None:
                # only searching by rel
                yield item
            elif item_name == name and item_rel == rel:
                # searching by name and rel
                yield item

    def find(self, name=None, rel=None):
        """Return a list of items in the array matching name and/or rel.

        If both name and rel parameters are provided, returned items must match
        both properties.

        """
        return list(self._matches(name=name, rel=rel))

    def get(self, name=None, rel=None):
        """Return the first item in the array matching name and/or rel.

        If both name and rel parameters are provided, the returned item must
        match both properties.

        If no item is found, raises ValueError.

        """
        try:
            return next(self._matches(name=name, rel=rel))
        except StopIteration:
            raise ValueError('No matching item found.')

    def to_dict(self):
        """Return a dictionary representing an Array object."""
        return {
            self.collection_name: [item.to_dict() for item in self]
        }


class Item(ComparableObject):

    """Object representing a Collection+JSON item object."""

    def __init__(self, href=None, data=None, links=None):
        self.href = href
        self.data = data
        self.links = links

    def __repr__(self):
        return "<Item: href='%s'>" % self.href

    def __getattr__(self, name):
        return getattr(self.data, name)

    @property
    def data(self):
        return self.__data

    @data.setter
    def data(self, value):
        self.__data = _from_iterable_to_array(Data, "data", value)

    @property
    def links(self):
        return self.__links

    @links.setter
    def links(self, value):
        self.__links = _from_iterable_to_array(Link, "links", value)

    @property
    def properties(self):
        """Return a list of names that can be looked up on the item."""
        return [item.name for item in self.data]

    def to_dict(self):
        """Return a dictionary representing an Item object."""
        output = {}
        if self.href:
            output['href'] = self.href
        if self.data:
            output.update(self.data.to_dict())
        if self.links:
            output.update(self.links.to_dict())
        return output


class Data(ComparableObject):

    """Object representing a Collection+JSON data object."""

    def __init__(self, name, value=None, prompt=None):
        self.name = name
        self.value = value
        self.prompt = prompt

    def __repr__(self):
        data = "name='%s'" % self.name
        if self.prompt is not None:
            data += " prompt='%s'" % self.prompt
        return "<Data: %s>" % data

    def to_dict(self):
        """Return a dictionary representing a Data object."""
        output = {
            'name': self.name
        }
        if self.value is not None:
            output['value'] = self.value
        if self.prompt is not None:
            output['prompt'] = self.prompt
        return output


class Query(ComparableObject):

    """Object representing a Collection+JSON query object."""

    def __init__(self, href, rel, name=None, prompt=None, data=None):
        self.href = href
        self.rel = rel
        self.name = name
        self.prompt = prompt
        self.data = data

    def __repr__(self):
        data = "rel='%s'" % self.rel
        if self.name:
            data += " name='%s'" % self.name
        if self.prompt:
            data += " prompt='%s'" % self.prompt
        return "<Query: %s>" % data

    @property
    def data(self):
        return self.__data

    @data.setter
    def data(self, value):
        self.__data = _from_iterable_to_array(Data, "data", value)

    def to_dict(self):
        """Return a dictionary representing a Query object."""
        output = {
            'href': self.href,
            'rel': self.rel,
        }
        if self.name is not None:
            output['name'] = self.name
        if self.prompt is not None:
            output['prompt'] = self.prompt
        if len(self.data):
            output.update(self.data.to_dict())
        return output


class Link(ComparableObject):

    """Object representing a Collection+JSON link object."""

    def __init__(self, href, rel, name=None, render=None, prompt=None):
        self.href = href
        self.rel = rel
        self.name = name
        self.render = render
        self.prompt = prompt

    def __repr__(self):
        data = "rel='%s'" % self.rel
        if self.name:
            data += " name='%s'" % self.name
        if self.render:
            data += " render='%s'" % self.render
        if self.prompt:
            data += " prompt='%s'" % self.prompt
        return "<Link: %s>" % data

    def to_dict(self):
        """Return a dictionary representing a Link object."""
        output = {
            'href': self.href,
            'rel': self.rel,
        }
        if self.name is not None:
            output['name'] = self.name
        if self.render is not None:
            output['render'] = self.render
        if self.prompt is not None:
            output['prompt'] = self.prompt
        return output
