"""
PDF Publication Date Mapping
Maps PDF filenames to their actual publication dates from PDF metadata
Auto-updated: 2025-11-20
"""

# PDFs with dates extracted from PDF metadata
PDF_DATES = {
    # 2025 PDFs
    "Jamf_Connect_Entra_2025.pdf": "2025-10-03",
    "Deploy_Apple_Beta.pdf": "2025-07-05",
    "Apple_Content_Caching.pdf": "2025-06-06",
    "apple-style-guide.pdf": "2025-06-03",
    "Travel_Data_Security.pdf": "2025-05-20",
    "Jamf_Microsoft_Platform_SSO.pdf": "2025-05-19",
    "Jamf_Health_Review.pdf": "2025-05-14",
    "JCE_Mac_Report.pdf": "2025-05-05",
    "System_Settings_Sequoia.pdf": "2025-03-30",
    "Jamf_Install_SentinalOne.pdf": "2025-03-18",
    "Offboard_Mac_Jamf.pdf": "2025-03-12",
    "Guide_iPadOS_18.pdf": "2025-03-06",
    "Account_Driven_Cloudflare.pdf": "2025-03-05",
    "Bootstrap_Token_Guide.pdf": "2025-03-04",
    "Jamf_SMTP_Google.pdf": "2025-01-14",
    "Jamf_SMTP_Microsoft_API.pdf": "2025-01-09",
    "Retrieve_AppleCare_Jamf_Cover.pdf": "2025-01-09",

    # 2024 PDFs
    "Change_Email_Address_Apple_Account.pdf": "2024-11-15",
    "macOS_Software_Update_Jamf.pdf": "2024-10-25",
    "SCIM_Token_ABM_Entra.pdf": "2024-10-24",
    "Jamf_Setup_Manager.pdf": "2024-09-27",
    "Outlook_365_for_Mac.pdf": "2024-07-12",
    "Getting_Started_Sonoma.pdf": "2024-06-14",
    "Jamf_Baseline.pdf": "2024-05-24",
    "Guide_to_iPadOS_17.pdf": "2024-05-09",
    "Archive_Emails_M365.pdf": "2024-05-07",
    "Enable_Touch_ID_Terminal.pdf": "2024-04-05",
    "Jamf_Printers.pdf": "2024-03-04",
    "Sysdiagnose.pdf": "2024-03-04",
    "Update_macOS_Managed.pdf": "2024-02-09",
    "Add_Mac_ABM_No_Erase.pdf": "2024-01-26",
    "Restore_Deleted_Objects.pdf": "2024-01-16",
    "Jamf_LAPS_Configure.pdf": "2024-01-04",

    # 2023 PDFs
    "Jamf_Smart_Group_Patch.pdf": "2023-12-26",
    "Jamf_Notifications_Slack.pdf": "2023-12-12",
    "System_Settings_Sonoma.pdf": "2023-11-17",
    "Enrolling_Org_ABMASM.pdf": "2023-11-09",
    "Sonoma_Blocker.pdf": "2023-11-08",
    "ABMASM_Verification.pdf": "2023-10-27",
    "Web_Browsers_Profiles.pdf": "2023-10-27",
    "Guide_to_iPadOS_16.pdf": "2023-09-20",
    "App_Password_Jamf.pdf": "2023-09-13",
    "erase-install.pdf": "2023-09-13",
    "macOS_Ventura_Getting_Started.pdf": "2023-09-10",
    "Jamf_Account_Driven.pdf": "2023-08-30",
    "Adobe_Pantone.pdf": "2023-08-28",
    "Scripting_Intro_Zsh.pdf": "2023-08-24",
    "Jamf_Escrow_Buddy.pdf": "2023-08-04",
    "Jamf_Pro_iOS_App_deploy_Silicon_Macs.pdf": "2023-06-23",
    "2FA_1Password.pdf": "2023-06-21",
    "ABM_Federation.pdf": "2023-06-21",
    "Managed_Apple_IDs.pdf": "2023-04-14",
    "Security_Key_Apple_ID.pdf": "2023-02-01",
    "System_Settings_Ventura.pdf": "2023-02-01",

    # 2022 PDFs
    "JamfGoogleCloud.pdf": "2022-12-02",
    "Manage_Background_Tasks_Jamf.pdf": "2022-10-24",
    "Jamf_Connect_Okta.pdf": "2022-10-07",
    "SIM_PIN.pdf": "2022-08-18",
    "Outlook_for_iPadOS.pdf": "2022-07-31",
    "Jamf_Teamviewer_Host.pdf": "2022-07-20",
    "Outlook_for_iOS_iPhone_2022.pdf": "2022-07-12",
    "HCS_ZIP_OneDrive.pdf": "2022-06-29",
    "Auto_Config_O365_Mail.pdf": "2022-05-26",
    "Deploying_Cisco_AnyConnect.pdf": "2022-05-18",
    "Integrate_TeamViewer_with_Jamf.pdf": "2022-03-07",
    "Jamf_ESET.pdf": "2022-01-25",

    # 2021 PDFs
    "Jamf_Connect_Azure.pdf": "2021-07-25",
    "Upgrade_Big_Sur_Jamf.pdf": "2021-07-08",
    "macOS_VMWare.pdf": "2021-05-31",
    "Deploy_Splashtop_Streamer_Jamf.pdf": "2021-03-09",

    # 2020 PDFs
    "Jamf_Connect_iDent_Azure.pdf": "2020-09-21",
    "Managing_Apple_Devices.pdf": "2020-07-26",
    "Wi-FI_Apple_Devices.pdf": "2020-07-24",
    "Jamf_Connect_GSuite.pdf": "2020-07-06",
    "Jamf_Splashbuddy.pdf": "2020-06-17",
    "Addigy_Deploying_Zoom.pdf": "2020-06-04",
    "Deploy_Zoom_Jamf.pdf": "2020-06-04",
    "Addigy_Microsoft365.pdf": "2020-05-13",
    "MAID_APNS_user.pdf": "2020-05-08",
    "Apple_Configurator_2_Blueprints.pdf": "2020-05-07",
    "Jamf_Pro_Intune.pdf": "2020-04-30",
    "How_to_add_ATV_to_ABM.pdf": "2020-04-21",
    "Google_Enterprise_Managed_Browser_Guide.pdf": "2020-04-14",
    "Google_SSO.pdf": "2020-03-31",
    "Upgrade_Catalina_Jamf.pdf": "2020-03-30",
    "Jamf_Kerberos.pdf": "2020-03-27",
    "Jamf_Google_App_Password.pdf": "2020-03-20",
    "Managing_Your_Apple_ID_HCS.pdf": "2020-03-06",

    # 2019 PDFs
    "How_to_use_Jamf_Helper.pdf": "2019-11-16",
    "Identity_Management_Azure_Jamf.pdf": "2019-11-15",
    "Set_Default_App_SS.pdf": "2019-08-22",
    "Signed_DEPNotify.pdf": "2019-07-17",
    "Enterprise_Connect.pdf": "2019-06-26",
    "Creating_VM.pdf": "2019-04-15",
    "Jamf_Autopkgr.pdf": "2019-04-01",
    "Jamf_Microsoft_Azure_Integration.pdf": "2019-03-20",
    "Jamf_Infrstructure_manager.pdf": "2019-03-14",
    "InPlace_macOS_Mojave_.pdf": "2019-01-31",

    # 2018 PDFs
    "JamfPro_AWS_Dist_Pt.pdf": "2018-09-18",
    "Jamf_SS_macOS_HS.pdf": "2018-06-19",
    "Jamf_Open_SSL.pdf": "2018-06-01",

    # All other PDFs are pre-2024 and will default to 'pre-2024'
}

def get_pdf_date(filename: str) -> str:
    """
    Get publication date for a PDF from metadata
    
    Args:
        filename: PDF filename
    
    Returns:
        ISO date string (YYYY-MM-DD) or 'pre-2024' for older content
    """
    return PDF_DATES.get(filename, 'pre-2024')

def is_recent_pdf(filename: str) -> bool:
    """Check if PDF is from 2024 or later"""
    date = get_pdf_date(filename)
    if date == 'pre-2024':
        return False
    try:
        year = int(date.split('-')[0])
        return year >= 2024
    except:
        return False

