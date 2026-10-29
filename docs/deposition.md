# Deposition approach

Checked against official guidance on 29 October 2026.

Scientific Data does not prescribe a single general-purpose repository for this
type of industrial dataset. Its requirements concern preservation, persistent
identifiers, reviewer access, direct downloads and open licences. CC0 and CC BY
are normally accepted; NC and SA restrictions are not generally allowed for
original non-sensitive datasets. Formal deposition is required from the second
review round; first-round sharing may use a seamless anonymous download.
[Scientific Data repository guidance](https://www.nature.com/sdata/policies/repositories)

For relevant custom code, the journal recommends GitHub together with a repository
that provides a persistent DOI. This project uses that approach; it is a project
choice, not a journal-mandated template.
[Scientific Data code policy](https://www.nature.com/sdata/policies/editorial-and-publishing-policies)

## Examples from Scientific Data

| Article | Deposited resources | Relevant practice |
|---|---|---|
| [A Dataset of Univariate Crimp Force Curves for Data-Driven Time Series Analysis](https://www.nature.com/articles/s41597-025-05858-0) (2025) | Harvard Dataverse; annotated DataFrame | A permanent data repository and explicit variable definitions |
| [Production Data Set for five-Axis CNC Milling with multiple Changeovers](https://www.nature.com/articles/s41597-025-05294-0) (2025) | CSV data in Zenodo; code and supporting materials on GitHub | Separate dataset and code access, production context and licence information |
| [Mondragon Unibertsitatea face-milling dataset for smart tool condition monitoring](https://www.nature.com/articles/s41597-025-05168-5) (2025) | Dataset at eBiltegia; processing scripts on GitHub | Named scripts, Python version and a requirements file |

These examples demonstrate different acceptable approaches. They are not a survey
of repository popularity. The present six CSVs remain CSVs; there is no need to
convert them to the pickle or MAT formats used by other authors.

## Chosen route

1. Maintain this repository on GitHub, with the six CSVs, metadata, processing and
   validation scripts, documentation and licences.
2. Build one public ZIP with `python scripts/build_archive.py`. It includes a
   manifest and excludes local source exports and unpublished manuscript files.
3. Create a Zenodo upload and select **Dataset** as the resource type. The archive
   contains both data and supporting code; Dataset reflects its principal purpose.
4. Use CC BY 4.0 for the dataset. Explain in the record description that the Python
   scripts are separately under MIT. Include both full licence texts in the ZIP.
5. Add creators, description, keywords, version and the GitHub URL. Reserve a new
   DOI for this object, then add it to the repository citation metadata before
   generating the final ZIP. Do not reuse a DOI belonging to another object.
6. Save a draft for review, or publish when ready. Include the actual DOI and
   accessible data/code locations in the manuscript.

Zenodo's upload guide permits mixed-object uploads and asks authors to choose
the resource type that best represents the upload. It also explains DOI reservation;
the reserved DOI is registered only when the record is published.
[Zenodo upload manual](https://help.zenodo.org/docs/deposit/create-new-upload/)

For confidential review, use Zenodo link sharing with preview permissions and
test downloading without logging in. Keep secret links outside the public Git
repository. Link expiry should allow sufficient time for review.
[Zenodo link-sharing manual](https://help.zenodo.org/docs/share/link-sharing/)

Automatic GitHub-to-Zenodo release archiving is an alternative for software.
It must be enabled before creating the release. This project uses a manual
Dataset deposit to make mixed data/code licensing and the upload contents explicit;
do not also create a duplicate automatic record for the same release by accident.
[Zenodo GitHub integration](https://help.zenodo.org/docs/github/enable-repository/)

## Remaining source-access issue

This public archive supports independent checks of the six CSVs and reproduces
Figures 3 and 4. Full source matching and Figure 2 require additional instrument
records. Those records have been prepared locally but are not part of this public
release. Arrange the permitted reviewer access or revise claims that depend on
inaccessible evidence before submission; a public DOI alone does not resolve that
issue. See [source access](source_access.md).
