"""
PDF Publication Date Mapping
Maps PDF filenames to their actual publication dates for recency-based search prioritization
Auto-updated: 2025-11-20
"""

# PDFs with known recent publication dates (2024+)
# Last scraped from https://hcsonline.com/support/resources/white-papers on 2025-11-20
RECENT_PDF_DATES = {
    # October 3, 2025 releases
    'Adobe_Pantone.pdf': '2025-10-03',
    'Jamf_Microsoft_Platform_SSO.pdf': '2025-10-03',
    'Identity_Management_Azure_Jamf.pdf': '2025-10-03',
    'MAID_APNS_user.pdf': '2025-10-03',
    'Change_Email_Address_Apple_Account.pdf': '2025-10-03',
    'Jamf_Infrstructure_manager.pdf': '2025-10-03',
    'Jamf_Connect_Entra.pdf': '2025-10-03',
    'Jamf_Connect_Entra_2025.pdf': '2025-10-03',  # Downloaded separately
    'macOS_Software_Update_Jamf.pdf': '2025-10-03',
    'How_to_add_ATV_to_ABM.pdf': '2025-10-03',
    'Archive_Emails_M365.pdf': '2025-10-03',
    'Jamf_Open_SSL.pdf': '2025-10-03',
    'Google_SSO.pdf': '2025-10-03',
    'Auto_Config_O365_Mail.pdf': '2025-10-03',
    'Jamf_Pro_iOS_App_deploy_Silicon_Macs.pdf': '2025-10-03',
    'Travel_Data_Security.pdf': '2025-10-03',
    'Jamf_Smart_Group_Patch.pdf': '2025-10-03',
    'Jamf_LAPS_Configure.pdf': '2025-10-03',
    'Passkeys.pdf': '2025-10-03',
    'Jamf_Connect_GSuite.pdf': '2025-10-03',
    '2FA_1Password.pdf': '2025-10-03',
    'Add_Mac_ABM_No_Erase.pdf': '2025-10-03',
    'ABM_Federation.pdf': '2025-10-03',
    'Sonoma_Blocker.pdf': '2025-10-03',
    'Jamf_Teamviewer_Host.pdf': '2025-10-03',
    'How_to_use_Jamf_Helper.pdf': '2025-10-03',
    'Security_Key_Apple_ID.pdf': '2025-10-03',
    'Deploy_Splashtop_Streamer_Jamf.pdf': '2025-10-03',
    'Jamf_Escrow_Buddy.pdf': '2025-10-03',
    'Jamf_Google_App_Password.pdf': '2025-10-03',
    'Set_Default_App_SS.pdf': '2025-10-03',
    'Jamf_ESET.pdf': '2025-10-03',
    'Addigy_Deploying_Zoom.pdf': '2025-10-03',
    'Bootstrap_Token_Guide.pdf': '2025-10-03',
    'Signed_DEPNotify.pdf': '2025-10-03',
    'Managed_Apple_IDs.pdf': '2025-10-03',
    'Creating_VM.pdf': '2025-10-03',
    'Managing_Your_Apple_ID_HCS.pdf': '2025-10-03',
    'JCE_Mac_Report.pdf': '2025-10-03',
    'SIM_PIN.pdf': '2025-10-03',
    'Jamf_Account_Driven.pdf': '2025-10-03',
    'SCIM_Token_ABM_Entra.pdf': '2025-10-03',
    'Jamf_SMTP_Microsoft_API.pdf': '2025-10-03',
    'Jamf_Printers.pdf': '2025-10-03',
    'erase-install.pdf': '2025-10-03',
    'Retrieve_AppleCare_Jamf_Cover.pdf': '2025-10-03',
    'Jamf_Setup_Manager.pdf': '2025-10-03',
    'macOS_VMWare.pdf': '2025-10-03',
    'Jamf_Kerberos.pdf': '2025-10-03',
    'Deploy_Zoom_Jamf.pdf': '2025-10-03',
}

def get_pdf_date(filename: str) -> str:
    """
    Get publication date for a PDF

    Args:
        filename: PDF filename

    Returns:
        ISO date string (YYYY-MM-DD) or 'pre-2024' for older content
    """
    return RECENT_PDF_DATES.get(filename, 'pre-2024')

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
