; Unatti Bank Reconciliation Tool
; Developed by Neuro Spark Work Solutions for Unatti Finserv
; Created with Inno Setup 6

[Setup]
; Basic Application Information
AppId={{UNATTI-BANK-RECON-2024-NEURO-SPARK}}
AppName=Unatti Bank Reconciliation Tool
AppVersion=1.0.0
AppVerName=Unatti Bank Reconciliation Tool v1.0.0
AppPublisher=Neuro Spark Work Solutions
AppPublisherURL=https://neurosparkworks.com
AppSupportURL=https://neurosparkworks.com/support
AppUpdatesURL=https://neurosparkworks.com/updates
AppCopyright=Copyright (C) 2024 Neuro Spark Work Solutions. Developed for Unatti Finserv.

; Installation Directories
DefaultDirName={autopf}\Unatti\BankReconciliationTool
DefaultGroupName=Unatti Bank Reconciliation Tool
AllowNoIcons=yes
DisableProgramGroupPage=yes

; Output Settings
OutputDir=..\installer_output
OutputBaseFilename=Unatti_BankReconciliationTool_Setup_v1.0.0
; SetupIconFile=..\assets\logo.ico  ; Commented out temporarily - icon file invalid

; Compression
Compression=lzma2/ultra64
SolidCompression=yes
InternalCompressLevel=ultra64

; Visual Settings
WizardStyle=modern
WizardSizePercent=120
DisableWelcomePage=no
ShowLanguageDialog=no

; License and Documentation
LicenseFile=LICENSE.txt
InfoBeforeFile=README_INSTALL.txt

; Uninstaller
UninstallDisplayIcon={app}\BankReconciliationApp.exe
CreateUninstallRegKey=yes
UninstallDisplayName=Unatti Bank Reconciliation Tool

; Privileges
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked
Name: "quicklaunchicon"; Description: "Create a &Quick Launch icon"; GroupDescription: "Additional icons:"; Flags: unchecked; OnlyBelowVersion: 6.1

[Files]
; Main application files - ONEDIR structure
Source: "..\dist\BankReconciliationTool\BankReconciliationApp.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\BankReconciliationTool\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\dist\BankReconciliationTool\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Sample data files (if available)
; Source: "..\src\bankLeasure.xlsx"; DestDir: "{app}\sample_data"; DestName: "sample_bank_ledger.xlsx"; Flags: ignoreversion
; Source: "..\examples\*"; DestDir: "{app}\examples"; Flags: ignoreversion recursesubdirs createallsubdirs

; Documentation
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "README_INSTALL.txt"; DestDir: "{app}"; DestName: "README.txt"; Flags: ignoreversion

[Dirs] 
; Create directories for user data
Name: "{app}\exports"; Permissions: users-full
Name: "{app}\data"; Permissions: users-full
Name: "{userappdata}\Unatti\BankReconciliationTool"; Permissions: users-full
Name: "{userappdata}\Unatti\BankReconciliationTool\exports"; Permissions: users-full

[Icons]
; Start Menu Icons
Name: "{group}\Unatti Bank Reconciliation Tool"; Filename: "{app}\BankReconciliationApp.exe"; WorkingDir: "{app}"; IconFilename: "{app}\BankReconciliationApp.exe"; Comment: "Unatti Bank Reconciliation - by Neuro Spark Work Solutions"
Name: "{group}\User Guide"; Filename: "{app}\README.txt"; Comment: "Installation and Usage Guide"
; Name: "{group}\Sample Data"; Filename: "{app}\sample_data"; Comment: "Sample Files for Testing"
Name: "{group}\Export Folder"; Filename: "{userappdata}\Unatti\BankReconciliationTool\exports"; Comment: "Default Export Location"
Name: "{group}\{cm:UninstallProgram,Unatti Bank Reconciliation Tool}"; Filename: "{uninstallexe}"; Comment: "Uninstall Unatti Bank Reconciliation Tool"

; Desktop Icon (optional)
Name: "{autodesktop}\Unatti Bank Reconciliation"; Filename: "{app}\BankReconciliationApp.exe"; WorkingDir: "{app}"; IconFilename: "{app}\BankReconciliationApp.exe"; Tasks: desktopicon; Comment: "Unatti Bank Reconciliation - by Neuro Spark Work Solutions"

; Quick Launch (for older Windows versions)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\Unatti Bank Reconciliation"; Filename: "{app}\BankReconciliationApp.exe"; Tasks: quicklaunchicon; Comment: "Unatti Bank Reconciliation Tool"

[Registry]
; Application settings
Root: HKCU; Subkey: "Software\Unatti\BankReconciliationTool"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"  
Root: HKCU; Subkey: "Software\Unatti\BankReconciliationTool"; ValueType: string; ValueName: "Version"; ValueData: "1.0.0"
Root: HKCU; Subkey: "Software\Unatti\BankReconciliationTool"; ValueType: string; ValueName: "DefaultExportPath"; ValueData: "{userappdata}\Unatti\BankReconciliationTool\exports"
Root: HKCU; Subkey: "Software\Unatti\BankReconciliationTool"; ValueType: string; ValueName: "Developer"; ValueData: "Neuro Spark Work Solutions"
Root: HKCU; Subkey: "Software\Unatti\BankReconciliationTool"; ValueType: string; ValueName: "Client"; ValueData: "Unatti Finserv"

; File associations (optional - for .xlsx files)
Root: HKCR; Subkey: ".unattirecon"; ValueType: string; ValueName: ""; ValueData: "UnattiBankReconciliationTool"; Flags: uninsdeletevalue

[Run]
; Option to run the program after installation
Filename: "{app}\BankReconciliationApp.exe"; Description: "{cm:LaunchProgram,Unatti Bank Reconciliation Tool}"; Flags: nowait postinstall skipifsilent; WorkingDir: "{app}"

[UninstallDelete]
; Clean up user data on uninstall (optional)
Type: filesandordirs; Name: "{userappdata}\Unatti\BankReconciliationTool\exports\*"
Type: files; Name: "{app}\*.log"

[Code]
// Custom Pascal script for advanced installation logic

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Create default export directory for Unatti
    CreateDir(ExpandConstant('{userappdata}\Unatti\BankReconciliationTool\exports'));
    
    // Set permissions for export directory
    // Additional post-install logic can go here
  end;
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
  // Add any pre-installation checks here
  
  // Check if .NET Framework is installed (if needed)
  // Check available disk space
  // Check Windows version compatibility
end;