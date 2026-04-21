#!/usr/bin/env python

__license__ = 'GPL v3'
__copyright__ = '2026, GitHub Copilot'

try:
    load_translations()
except NameError:
    pass

import os

from lxml import etree

from calibre.customize import MetadataWriterPlugin

NS_OPF = 'http://www.idpf.org/2007/opf'
SERIES_COLLECTION_ID = 'komga-series-collection'


def _opf_tag(name):
    return f'{{{NS_OPF}}}{name}'


def _text(node):
    return (node.text or '').strip()


def _iter_meta_nodes(metadata):
    return [child for child in metadata if child.tag == _opf_tag('meta')]


def _find_metadata_node(root):
    for child in root:
        if child.tag == _opf_tag('metadata'):
            return child
    return None


def _find_spine_node(root):
    for child in root:
        if child.tag == _opf_tag('spine'):
            return child
    return None


def _find_refines(metadata, collection_id):
    ref = f'#{collection_id}'
    return [node for node in _iter_meta_nodes(metadata) if node.get('refines') == ref]


def _remove_series_collections(metadata):
    removed = False
    for node in list(_iter_meta_nodes(metadata)):
        if node.get('property') != 'belongs-to-collection':
            continue

        collection_id = node.get('id')
        if not collection_id:
            continue

        refines = _find_refines(metadata, collection_id)
        properties = {refine.get('property'): _text(refine) for refine in refines}
        if properties.get('collection-type') != 'series' and collection_id != SERIES_COLLECTION_ID:
            continue

        for refine in refines:
            metadata.remove(refine)
        metadata.remove(node)
        removed = True

    return removed


def _insert_meta(metadata, index, text=None, **attributes):
    node = metadata.makeelement(_opf_tag('meta'), attrib=attributes)
    if text is not None:
        node.text = text
    metadata.insert(index, node)
    return index + 1


def _first_meta_index(metadata):
    for index, child in enumerate(metadata):
        if child.tag == _opf_tag('meta'):
            return index
    return len(metadata)


def _format_series_index(value):
    try:
        return str(float(value))
    except Exception:
        return '1.0'


def _normalize_direction(value):
    if not isinstance(value, str):
        return None
    direction = value.strip().lower()
    if direction in {'rtl', 'ltr'}:
        return direction
    if direction.endswith('-rl'):
        return 'rtl'
    if direction.endswith('-lr'):
        return 'ltr'
    return None


def _infer_page_progression_direction(metadata, spine, mi):
    direction = _normalize_direction(getattr(mi, 'page_progression_direction', None))
    if direction:
        return direction

    if spine is not None:
        direction = _normalize_direction(spine.get('page-progression-direction'))
        if direction:
            return direction

    direction = _normalize_direction(getattr(mi, 'primary_writing_mode', None))
    if direction:
        return direction

    for node in _iter_meta_nodes(metadata):
        if node.get('name') == 'primary-writing-mode':
            direction = _normalize_direction(node.get('content'))
            if direction:
                return direction

    return None


def write_komga_series_collection_metadata(stream, mi):
    from calibre.ebooks.metadata.epub import LocalZipFile
    from calibre.ebooks.metadata.epub import get_zip_reader
    from calibre.ebooks.metadata.opf2 import OPF
    from calibre.ebooks.metadata.utils import pretty_print_opf
    from calibre.utils.xml_parse import safe_xml_fromstring
    from calibre.utils.zipfile import safe_replace

    if hasattr(stream, 'seek'):
        stream.seek(0)

    reader = get_zip_reader(stream, root=os.getcwd())
    root = safe_xml_fromstring(reader.read_bytes(reader.opf_path))
    metadata = _find_metadata_node(root)
    if metadata is None:
        return
    spine = _find_spine_node(root)

    changed = _remove_series_collections(metadata)

    series = getattr(mi, 'series', None)
    series = series.strip() if isinstance(series, str) else series
    if series:
        index = _first_meta_index(metadata)
        index = _insert_meta(
            metadata,
            index,
            text=series,
            property='belongs-to-collection',
            id=SERIES_COLLECTION_ID,
        )
        index = _insert_meta(
            metadata,
            index,
            text='series',
            refines=f'#{SERIES_COLLECTION_ID}',
            property='collection-type',
        )
        _insert_meta(
            metadata,
            index,
            text=_format_series_index(getattr(mi, 'series_index', None)),
            refines=f'#{SERIES_COLLECTION_ID}',
            property='group-position',
        )
        changed = True

    if spine is not None:
        direction = _infer_page_progression_direction(metadata, spine, mi)
        if direction and spine.get('page-progression-direction') != direction:
            spine.set('page-progression-direction', direction)
            changed = True

    if not changed:
        return

    pretty_print_opf(root)
    opf_bytes = etree.tostring(root, encoding='utf-8', xml_declaration=True, pretty_print=True)

    if isinstance(reader.archive, LocalZipFile):
        reader.archive.safe_replace(reader.container[OPF.MIMETYPE], opf_bytes, add_missing=True)
    else:
        safe_replace(stream, reader.container[OPF.MIMETYPE], opf_bytes, add_missing=True)


class KomgaEpubMetadataWriter(MetadataWriterPlugin):
    name = 'Komga EPUB Compatibility Writer'
    description = 'Add Komga-compatible EPUB metadata for series grouping and reading direction.'
    supported_platforms = ['windows', 'osx', 'linux']
    author = 'Alysson Souza'
    version = (0, 1, 0)
    minimum_calibre_version = (5, 0, 0)
    file_types = {'epub', 'kepub'}

    def set_metadata(self, stream, mi, ftype):
        from calibre.customize.builtins import EPUBMetadataWriter
        from calibre.customize.ui import apply_null_metadata
        from calibre.customize.ui import config
        from calibre.customize.ui import find_plugin
        from calibre.customize.ui import force_identifiers

        if hasattr(stream, 'seek'):
            stream.seek(0)

        calibre_writer = find_plugin(EPUBMetadataWriter.name)
        calibre_writer.apply_null = apply_null_metadata.apply_null
        calibre_writer.force_identifiers = force_identifiers.force_identifiers
        calibre_writer.site_customization = config['plugin_customization'].get(calibre_writer.name, '')
        calibre_writer.set_metadata(stream, mi, ftype)

        if hasattr(stream, 'seek'):
            stream.seek(0)
        write_komga_series_collection_metadata(stream, mi)
