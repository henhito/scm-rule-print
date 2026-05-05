SCM Rule Browser Script

This Python script connects to Palo Alto Networks Strata Cloud Manager (SCM) and helps you browse firewall rules across folders and devices, filter them, and export the results to CSV. It automates the process of retrieving the SCM scope tree (folders and devices), displaying security rules, filtering them by keywords, and exporting selected rules to a CSV file with the same columns as displayed in the SCM UI.

What the script does
Authenticate using an OAuth client (SCM_CLIENT_ID / SCM_CLIENT_SECRET) with your tenant scope (SCM_TSG_ID).
Retrieve folders and devices from your tenant and display them as a tree so you can choose a scope.
List security rules within the selected folder or device, showing key columns such as name, tags, source, destination, application, service, category, action, profile, options, target, usage, and modified/created timestamps.
Filter rules by any term across all fields. For example, you can search for a device name, a user, an address, a tag, an application (e.g. dns), or a rule action (allow).
Export rules to a CSV file containing exactly the columns you see in SCM.

Requirements
Python 3.10 or later recommended
Internet access to the SCM API
A valid SCM API client with:
`SCM_CLIENT_ID`
`SCM_CLIENT_SECRET`
`SCM_TSG_ID`
Python package required
Install the dependency:
```powershell
python -m pip install requests
```
File naming
Make sure the script file ends in `.py`, not `.phy`.
Example:
```powershell
rule-print02.py
```
Secrets file
Create a file called `secrets.json` in the same folder as the script.
Example:
```json
{
  "SCM_CLIENT_ID": "your-client-id",
  "SCM_CLIENT_SECRET": "your-client-secret",
  "SCM_TSG_ID": "your-tsg-id"
}
```
How to run the script
From PowerShell:
```powershell
python .\rule-print02.py
```
What you will see
When the script starts it will:
Authenticate to SCM
Retrieve folders
Retrieve full folder details
Retrieve devices
Display the folder / device tree
Let you select a number
Example:
```text
SCM Scope and Rule Browser
--------------------------
Authenticating to SCM...
Retrieving folders...
Retrieving full folder details...
Retrieving devices...

Available folders in this SCM tenant:

  1. Global
  2. └── All
  3.     ├── Cloud-Provider-01
  4.     │   ├── COP01-External_01
  5.     │   │   └── CP01-FW-02
  6.     │   └── COP01-Internal_01
  7.     │       └── CP01-FW-01
  8.     │           └── [device] CP01-FW01
  9.     ├── DCOP01-UK-External
 10.     │   └── DCOP01-FW01
 11.     │       └── [device] PA-410
 12.     └── DCOP02-DE-External
 13.         └── DCOP01-FW02
 14.             └── [device] PA-440

Q. Quit
```
Menu options
After selecting a scope, the script shows the rules and gives these options:
`E` = export the currently displayed rules to CSV
`F` = filter the currently displayed rules
`R` = return to the main menu
`Q` = quit
Filtering example
If you press:
```text
F
```
The script asks for a search term.
Examples:
```text
dns
```
```text
allow
```
```text
CP01-FW-01
```
```text
Outbound_1
```
The filter checks all displayed/exported rule fields and only keeps matching rules.
Press Enter on a blank filter to clear the filter and show all rules again.
CSV export behavior
When you press:
```text
E
```
the script exports the currently displayed rules only.
That means:
if no filter is active, all rules in the selected scope are exported
if a filter is active, only the filtered rules are exported
CSV columns exported
The script exports these columns only:
Name
Tags
Source Zone
Source Address
Source User
Source Device
Destination Zone
Destination Address
Application
Service
URL Category
Action
Profile
Options
Target
Rule Usage
Rule Usage Apps Seen
Modified
Created
CSV export examples
Example 1: Export all rules in a folder
Select the folder:
```text
   10
   ```
Review the rules
Press:
```text
   E
   ```
Example output:
```text
Export complete. 7 rule(s) written to 'security_rules_CP01-FW-01_20260501_143210.csv'.
```
Example 2: Filter for DNS rules, then export only those
Select a folder
Press:
```text
   F
   ```
Enter:
```text
   dns
   ```
The displayed rules will now only show DNS-related matches
Press:
```text
   E
   ```
Example output:
```text
Export complete. 2 rule(s) written to 'security_rules_CP01-FW-02_20260501_143455.csv'.
```
Example 3: Filter by profile name, then export
Press:
```text
   F
   ```
Enter:
```text
   Outbound_1
   ```
Press:
```text
   E
   ```
Example output:
```text
Export complete. 3 rule(s) written to 'security_rules_COP01-Internal_01_20260501_144005.csv'.
```
Example CSV content
Example CSV output:
```csv
Name,Tags,Source Zone,Source Address,Source User,Source Device,Destination Zone,Destination Address,Application,Service,URL Category,Action,Profile,Options,Target,Rule Usage,Rule Usage Apps Seen,Modified,Created
Internet Access,,Trusted,any,any,,Untrusted,any,any,application-default,any,allow,Outbound_1,,,"",,2026-04-28T10:11:52Z,2025-06-02T08:17:21Z
DNS Access,,Trusted,any,any,,Untrusted,any,dns,application-default,any,allow,Outbound_1,log-end,,,"",2026-04-28T10:12:10Z,2025-06-02T08:18:03Z
```
Debug files created
The script writes these files to help troubleshoot the SCM tree structure:
`scm_folders_list_debug.json`
`scm_folders_enriched_debug.json`
`scm_devices_debug.json`
Use these if:
the parent / child tree looks wrong
devices attach under the wrong folder
the scope hierarchy does not match the SCM UI
Common issues
1. `ModuleNotFoundError: No module named 'requests'`
Install the package:
```powershell
python -m pip install requests
```
2. Folder tree looks flat
Check these files:
`scm_folders_list_debug.json`
`scm_folders_enriched_debug.json`
`scm_devices_debug.json`
That usually means the SCM API payload is not exposing the parent-child relationship in the field the script expects.
3. Some exported columns are blank
Columns like these may be empty if the SCM API response does not return them directly for that rule:
Profile
Options
Target
Rule Usage
Rule Usage Apps Seen
Recommended usage flow
Run the script
Choose a scope
Filter if needed
Export the visible result set
Review the CSV in Excel
Notes
The script exports only valid rules with a real action
The script does not permanently store CSVs outside the folder where it is run
CSV files are named automatically with the scope name and timestamp
