# Komga EPUB Metadata Writer

External Calibre plugin that enriches **Save to Disk** EPUB exports with metadata fields used by Komga.

## Features

- adds EPUB collection metadata for series name and series index
- preserves Calibre's normal EPUB metadata writing
- adds `page-progression-direction` when it can be derived from available writing-mode metadata
- works with `epub` and `kepub`

## Metadata written for Komga

The plugin adds these EPUB fields when series information is available:

```xml
<meta property="belongs-to-collection" id="komga-series-collection">Series Name</meta>
<meta refines="#komga-series-collection" property="collection-type">series</meta>
<meta refines="#komga-series-collection" property="group-position">11.0</meta>
```

When a reading direction can be determined, it also ensures the OPF spine contains:

```xml
<spine page-progression-direction="rtl">
```

## Installation

1. Download the latest `komga-epub-metadata-writer-vX.Y.Z.zip` from the repository's **Releases** page.

2. In Calibre, open:

   `Preferences -> Plugins -> Load plugin from file`

3. Select:

   the downloaded `komga-epub-metadata-writer-vX.Y.Z.zip`

4. Restart Calibre.

## Usage

1. In Calibre, keep **Save to Disk** configured to update metadata in exported files.
2. In `Preferences -> Import/export -> Saving books to disk`, set the save template to:

   ```text
   program:
       if field('series') then
           strcat(
               field('series'), '/',
               finish_formatting(field('series_index'), '0>2s', '', ' - '),
               field('title'), ' - ', field('authors')
           )
       else
           strcat(
               field('author_sort'), '/',
               field('title'), '/',
               field('title'), ' - ', field('authors')
           )
       fi
   ```

   This keeps all books in the same series under one shared series folder, which is what Komga uses to group them. It avoids splitting a series when different volumes have different `author_sort` values, while still keeping standalone books under their author and title folders.

   Example output:

   - `Foundation/01 - Foundation - Isaac Asimov.epub`
   - `Foundation/02 - Foundation and Empire - Isaac Asimov.epub`
   - `Asimov, Isaac/The Caves of Steel/The Caves of Steel - Isaac Asimov.epub`

3. Export EPUB books with **Save to Disk**.
4. Let Komga scan or refresh the target library.

## Releases

- Versioned plugin ZIP files are attached to GitHub Releases.
- Download the latest release asset and load it directly in Calibre.

## Build from source

If you want to build the plugin yourself:

  ```sh
  make build
  ```

## Verification

Komga reads metadata from the **embedded OPF inside the EPUB file**.

To verify the plugin output, inspect the OPF inside the exported `.epub` and confirm that the collection metadata is present.
