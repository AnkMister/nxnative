# Integration storage

The private NuGet package cache was cleared with dotnet's cache command using
only the task's exact NUGET_PACKAGES root. After verifying no tracked files,
Git metadata, open files or process working directories in each candidate,
37 generated roots were removed. The [root inventory](storage-cleanup.json)
uses paths relative to the external integration evidence root.

Removed roots are the private downloaded feed, four publish directories and
bin/obj outputs in the four isolated source snapshots. Source snapshots, package
age/SHA audits, scripts, compiler and test logs, fingerprints, PR file lists and
failed-attempt evidence remain in the external oot-hyper/ and oot-hyper-main/
evidence folders. No shared package cache or unknown artifact was removed.

Checkout outputs remain because the harness working directory is in this
checkout: dm/host/dmhost, dm/host/gen/, dm/host/tests/build/ and the native
executables and symbols under dm/gfx/tests/. These are ignored build products;
source, Git and all committed records are retained. The protected baseline and
game folders were never written. No game or full shader build ran.
