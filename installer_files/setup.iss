; Unnatti Bank Reconciliation Tool
; Developed by Neuro Spark Work Solutions for Unnatti Finserv
; Created with Inno Setup 6

[Setup]
; Basic Application Information
AppId={{UNNATTI-BANK-RECON-2024-NEURO-SPARK}}
AppName=Unnatti Bank Reconciliation Tool
AppVersion=1.0.0
AppVerName=Unnatti Bank Reconciliation Tool v1.0.0
AppPublisher=Neuro Spark Work Solutions
AppPublisherURL=https://neurosparkworks.com
AppSupportURL=https://neurosparkworks.com/support
AppUpdatesURL=https://neurosparkworks.com/updates
AppCopyright=Copyright (C) 2024 Neuro Spark Work Solutions. Developed for Unnatti Finserv.

; Installation Directories
DefaultDirName={autopf}\Unnatti\BankReconciliationTool
DefaultGroupName=Unnatti Bank Reconciliation Tool
AllowNoIcons=yes
DisableProgramGroupPage=yes

; Output Settings
OutputDir=..\installer_output
OutputBaseFilename=Unnatti_BankReconciliationTool_Setup_v1.0.0
SetupIconFile=..\assets\logo.ico

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
; LicenseFile=LICENSE.txt
; InfoBeforeFile=README_INSTALL.txt

; Uninstaller
UninstallDisplayIcon={app}\BankReconciliationTool.exe
CreateUninstallRegKey=yes
UninstallDisplayName=Unnatti Bank Reconciliation Tool

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
Source: "..\dist\BankReconciliationTool\BankReconciliationTool.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\BankReconciliationTool\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\dist\BankReconciliationTool\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Sample data files (if available)
; Source: "..\src\bankLeasure.xlsx"; DestDir: "{app}\sample_data"; DestName: "sample_bank_ledger.xlsx"; Flags: ignoreversion
; Source: "..\examples\*"; DestDir: "{app}\examples"; Flags: ignoreversion recursesubdirs createallsubdirs

; Documentation
; Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion
; Source: "README_INSTALL.txt"; DestDir: "{app}"; DestName: "README.txt"; Flags: ignoreversion

[Dirs] 
; Create directories for user data
Name: "{app}\exports"; Permissions: users-full
Name: "{app}\data"; Permissions: users-full
Name: "{userappdata}\Unnatti\BankReconciliationTool"; Permissions: users-full
Name: "{userappdata}\Unnatti\BankReconciliationTool\exports"; Permissions: users-full

[Icons]
; Start Menu Icons
Name: "{group}\Unnatti Bank Reconciliation Tool"; Filename: "{app}\BankReconciliationTool.exe"; WorkingDir: "{app}"; IconFilename: "{app}\BankReconciliationTool.exe"; Comment: "Unnatti Bank Reconciliation - by Neuro Spark Work Solutions"
; Name: "{group}\User Guide"; Filename: "{app}\README.txt"; Comment: "Installation and Usage Guide"
; Name: "{group}\Sample Data"; Filename: "{app}\sample_data"; Comment: "Sample Files for Testing"
Name: "{group}\Export Folder"; Filename: "{userappdata}\Unnatti\BankReconciliationTool\exports"; Comment: "Default Export Location"
Name: "{group}\{cm:UninstallProgram,Unnatti Bank Reconciliation Tool}"; Filename: "{uninstallexe}"; Comment: "Uninstall Unnatti Bank Reconciliation Tool"

; Desktop Icon (optional)
Name: "{autodesktop}\Unnatti Bank Reconciliation"; Filename: "{app}\BankReconciliationTool.exe"; WorkingDir: "{app}"; IconFilename: "{app}\BankReconciliationTool.exe"; Tasks: desktopicon; Comment: "Unnatti Bank Reconciliation - by Neuro Spark Work Solutions"

; Quick Launch (for older Windows versions)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\Unnatti Bank Reconciliation"; Filename: "{app}\BankReconciliationTool.exe"; Tasks: quicklaunchicon; Comment: "Unnatti Bank Reconciliation Tool"

[Registry]
; Application settings
Root: HKCU; Subkey: "Software\Unnatti\BankReconciliationTool"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"  
Root: HKCU; Subkey: "Software\Unnatti\BankReconciliationTool"; ValueType: string; ValueName: "Version"; ValueData: "1.0.0"
Root: HKCU; Subkey: "Software\Unnatti\BankReconciliationTool"; ValueType: string; ValueName: "DefaultExportPath"; ValueData: "{userappdata}\Unnatti\BankReconciliationTool\exports"
Root: HKCU; Subkey: "Software\Unnatti\BankReconciliationTool"; ValueType: string; ValueName: "Developer"; ValueData: "Neuro Spark Work Solutions"
Root: HKCU; Subkey: "Software\Unnatti\BankReconciliationTool"; ValueType: string; ValueName: "Client"; ValueData: "Unnatti Finserv"

; File associations (optional - for .xlsx files)
Root: HKCR; Subkey: ".unnattirecon"; ValueType: string; ValueName: ""; ValueData: "UnnattiBankReconciliationTool"; Flags: uninsdeletevalue

[Run]
; Option to run the program after installation
Filename: "{app}\BankReconciliationTool.exe"; Description: "{cm:LaunchProgram,Unnatti Bank Reconciliation Tool}"; Flags: nowait postinstall skipifsilent; WorkingDir: "{app}"

[UninstallDelete]
; Clean up user data on uninstall (optional)
Type: filesandordirs; Name: "{userappdata}\Unnatti\BankReconciliationTool\exports\*"
Type: files; Name: "{app}\*.log"

[Code]
// Custom Pascal script for advanced installation logic

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Create default export directory for Unnatti
    CreateDir(ExpandConstant('{userappdata}\Unnatti\BankReconciliationTool\exports'));
    
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