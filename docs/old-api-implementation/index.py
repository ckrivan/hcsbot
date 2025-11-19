from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
from openai import OpenAI
from typing import List, Dict, Any

# Updated with new OpenAI API key - 2025-11-19

# Try to import RAG system, but make it optional for Vercel deployment
try:
    from rag_system import rag_system
    RAG_AVAILABLE = True
    logger_temp = logging.getLogger(__name__)
    logger_temp.info("RAG system imported successfully")
except Exception as e:
    RAG_AVAILABLE = False
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning(f"RAG system not available: {e}. Using static knowledge only.")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

@app.route('/api/ping')
def ping():
    """Simple ping endpoint to verify app is running"""
    return jsonify({"status": "ok", "message": "API is alive"})

class ChatService:
    def __init__(self):
        self.initialized = False
        self.openai_client = None
        self.rag_initialized = False
        
    def initialize(self):
        """Initialize the chat service with AI client and RAG system"""
        # Initialize OpenAI client (required)
        try:
            openai_key = os.getenv('OPENAI_API_KEY')
            logger.info(f"OpenAI API key present: {openai_key is not None}")
            if openai_key:
                logger.info(f"OpenAI API key length: {len(openai_key)}")
                logger.info(f"OpenAI API key starts with: {openai_key[:10]}...")
                try:
                    self.openai_client = OpenAI(api_key=openai_key)
                    logger.info("OpenAI client created successfully")
                    # Test the client
                    logger.info("OpenAI client type: " + str(type(self.openai_client)))
                    logger.info("OpenAI client is not None: " + str(self.openai_client is not None))
                except Exception as init_error:
                    logger.error(f"Error creating OpenAI client: {init_error}")
                    logger.error(f"Error type: {type(init_error)}")
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    self.openai_client = None
            else:
                logger.warning("No OpenAI API key found in environment")
                self.openai_client = None
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client (outer): {e}")
            import traceback
            logger.error(f"Outer traceback: {traceback.format_exc()}")
            self.openai_client = None

        # Initialize RAG system (optional - don't fail if this doesn't work)
        try:
            if RAG_AVAILABLE:
                logger.info("Initializing RAG system...")
                self.rag_initialized = rag_system.initialize()
                if self.rag_initialized:
                    logger.info("RAG system initialized successfully")
                else:
                    logger.warning("RAG system initialization failed, falling back to static knowledge")
            else:
                logger.warning("RAG system not available, using static knowledge only")
                self.rag_initialized = False
        except Exception as e:
            logger.error(f"Failed to initialize RAG system: {e}")
            self.rag_initialized = False

        # Mark as initialized regardless of RAG status
        self.initialized = True
        logger.info(f"Chat service initialized: OpenAI={'available' if self.openai_client else 'unavailable'}, RAG={'enabled' if self.rag_initialized else 'disabled'}")
    
    def search_knowledge_base(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Search knowledge base using RAG system or fallback to static knowledge"""
        
        # Use RAG system if available
        if self.rag_initialized and RAG_AVAILABLE:
            logger.info(f"Using RAG system for query: {query}")
            try:
                results = rag_system.semantic_search(query, top_k=max_results)
                if results:
                    logger.info(f"RAG system found {len(results)} results")
                    return results
                else:
                    logger.warning("RAG system returned no results, falling back to static knowledge")
            except Exception as e:
                logger.error(f"RAG system search failed: {e}, falling back to static knowledge")
        
        # Fallback to static knowledge base with intent recognition
        logger.info("Using static knowledge base with intent recognition")
        query_lower = query.lower()
        
        # Extract intent from query
        install_intent = any(word in query_lower for word in ['install', 'deployment', 'deploy', 'setup', 'configure'])
        troubleshoot_intent = any(word in query_lower for word in ['troubleshoot', 'fix', 'error', 'problem', 'issue', 'not working'])
        config_intent = any(word in query_lower for word in ['configure', 'config', 'settings', 'setup'])
        
        knowledge_chunks = [
            {
                'text': 'Learn how to create and implement Passkeys for enhanced security authentication. Passkeys provide a passwordless authentication experience using biometric verification and cryptographic keys, replacing traditional passwords with more secure and user-friendly authentication methods.',
                'source': 'Passkeys.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Passkeys.pdf',
                'page': 1,
                'keywords': ['passkeys', 'authentication', 'security', 'passwordless', 'biometric', 'cryptographic', 'login']
            },
            {
                'text': 'Deploy Apple Software Beta Updates with Jamf Pro Blueprints without requiring an Apple Account. This guide covers beta deployment strategies, configuration management, and testing procedures for organizations wanting to evaluate new Apple software features.',
                'source': 'Deploy_Apple_Beta.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Deploy_Apple_Beta.pdf',
                'page': 1,
                'keywords': ['apple beta', 'software updates', 'jamf pro', 'deployment', 'testing', 'beta program', 'configuration']
            },
            {
                'text': 'Travel and Border Crossing Data Security Considerations for mobile devices and data protection. Essential guidelines for securing corporate data when crossing international borders, including encryption requirements and data handling procedures.',
                'source': 'Travel_Data_Security.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Travel_Data_Security.pdf',
                'page': 1,
                'keywords': ['travel security', 'border crossing', 'data protection', 'mobile security', 'encryption', 'compliance', 'international']
            },
            {
                'text': 'Configure Jamf Pro and Intune Company Portal for macOS Platform SSO Integration. This guide covers setting up seamless single sign-on between Jamf Pro and Microsoft Intune, enabling unified identity management across platforms.',
                'source': 'Jamf_Microsoft_Platform_SSO.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Jamf_Microsoft_Platform_SSO.pdf',
                'page': 1,
                'keywords': ['jamf pro', 'intune', 'platform sso', 'single sign-on', 'microsoft', 'macos', 'identity management', 'integration']
            },
            {
                'text': 'Configure Jamf Compliance Editor and Jamf Pro for comprehensive Mac compliance reporting. Set up automated compliance monitoring, policy enforcement, and detailed reporting for Mac computers in enterprise environments.',
                'source': 'JCE_Mac_Report.pdf',
                'url': 'https://hcsonline.com/images/PDFs/JCE_Mac_Report.pdf',
                'page': 1,
                'keywords': ['jamf compliance editor', 'compliance reporting', 'mac compliance', 'policy enforcement', 'monitoring', 'enterprise']
            },
            {
                'text': 'Offboard a Mac Computer using Jamf Pro and Apple Business Manager. Complete guide for securely removing Mac computers from management, including data wiping, certificate removal, and Apple Business Manager cleanup procedures.',
                'source': 'Offboard_Mac_Jamf.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Offboard_Mac_Jamf.pdf',
                'page': 1,
                'keywords': ['offboard', 'mac computer', 'jamf pro', 'apple business manager', 'device removal', 'data wipe', 'cleanup']
            },
            {
                'text': 'Configure Jamf Pro SMTP with Google Authentication for email notifications and reporting. Set up secure email integration using Google Workspace authentication for Jamf Pro communications and automated reports.',
                'source': 'Jamf_SMTP_Google.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Jamf_SMTP_Google.pdf',
                'page': 1,
                'keywords': ['jamf pro', 'smtp', 'google authentication', 'email notifications', 'google workspace', 'integration', 'reporting']
            },
            {
                'text': 'Configure Jamf Pro SMTP to use the Microsoft Graph API for enhanced email integration. Implement modern authentication with Microsoft 365 for Jamf Pro email notifications, reports, and communication features.',
                'source': 'Jamf_SMTP_Microsoft_API.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Jamf_SMTP_Microsoft_API.pdf',
                'page': 1,
                'keywords': ['jamf pro', 'smtp', 'microsoft graph api', 'microsoft 365', 'email integration', 'modern authentication', 'notifications']
            },
            {
                'text': 'Retrieve AppleCare Expiration information for Mac Computers using Jamf Pro. Automate AppleCare warranty status monitoring, generate reports on coverage expiration dates, and maintain hardware support visibility across your Mac fleet.',
                'source': 'Retrieve_AppleCare_Jamf_Cover.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Retrieve_AppleCare_Jamf_Cover.pdf',
                'page': 1,
                'keywords': ['applecare', 'warranty', 'expiration', 'mac computers', 'jamf pro', 'hardware support', 'monitoring', 'reporting']
            },
            {
                'text': 'Account-Driven Enrollment Methods with Apple Devices Using Cloudflare for secure device onboarding. Configure automated enrollment processes with Cloudflare integration for streamlined device management and authentication.',
                'source': 'Account_Driven_Cloudflare.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Account_Driven_Cloudflare.pdf',
                'page': 1,
                'keywords': ['account driven enrollment', 'apple devices', 'cloudflare', 'device onboarding', 'automated enrollment', 'authentication']
            },
            {
                'text': 'Renew your SCIM Token for Directory Sync between Apple Business Manager and Microsoft Entra ID. Maintain seamless directory synchronization by properly managing SCIM token renewals and authentication.',
                'source': 'SCIM_Token_ABM_Entra.pdf',
                'url': 'https://hcsonline.com/images/PDFs/SCIM_Token_ABM_Entra.pdf',
                'page': 1,
                'keywords': ['scim token', 'directory sync', 'apple business manager', 'microsoft entra id', 'authentication', 'renewal']
            },
            {
                'text': 'Deploy and Configure Jamf Setup Manager for automated device setup and user onboarding. Streamline the out-of-box experience with customized setup workflows and configuration management.',
                'source': 'Jamf_Setup_Manager.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Jamf_Setup_Manager.pdf',
                'page': 1,
                'keywords': ['jamf setup manager', 'device setup', 'automated setup', 'user onboarding', 'configuration management', 'out of box']
            },
            {
                'text': 'Configure Software Update Settings for macOS in Jamf Pro. Manage macOS updates, deferrals, and installation policies to maintain system security while minimizing user disruption.',
                'source': 'macOS_Software_Update_Jamf.pdf',
                'url': 'https://hcsonline.com/images/PDFs/macOS_Software_Update_Jamf.pdf',
                'page': 1,
                'keywords': ['macos', 'software updates', 'jamf pro', 'update management', 'deferrals', 'installation policies', 'system security']
            },
            {
                'text': 'Configure Baseline settings for Jamf Pro to establish consistent device management standards. Set up foundational policies, configurations, and security baselines across your Apple device fleet.',
                'source': 'Jamf_Baseline.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Jamf_Baseline.pdf',
                'page': 1,
                'keywords': ['jamf baseline', 'device management', 'baseline configuration', 'policies', 'security standards', 'fleet management']
            },
            {
                'text': 'Setup Email Archiving in Microsoft 365 for compliance and data retention. Configure automated email archiving, retention policies, and legal hold features for enterprise compliance requirements.',
                'source': 'Archive_Emails_M365.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Archive_Emails_M365.pdf',
                'page': 1,
                'keywords': ['email archiving', 'microsoft 365', 'compliance', 'data retention', 'retention policies', 'legal hold']
            },
            {
                'text': 'Enable Touch ID in Terminal for enhanced security and convenience. Configure biometric authentication for Terminal commands and sudo operations on macOS systems.',
                'source': 'Enable_Touch_ID_Terminal.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Enable_Touch_ID_Terminal.pdf',
                'page': 1,
                'keywords': ['touch id', 'terminal', 'biometric authentication', 'security', 'sudo', 'macos', 'authentication']
            },
            {
                'text': 'Deploy Printers with Jamf Pro for centralized print management. Configure printer deployment, driver installation, and print queue management across your Mac fleet using Jamf Pro policies.',
                'source': 'Jamf_Printers.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Jamf_Printers.pdf',
                'page': 1,
                'keywords': ['printer deployment', 'jamf pro', 'print management', 'driver installation', 'print queue', 'mac fleet', 'policies']
            },
            {
                'text': 'Update macOS Sonoma Using Managed Software Updates in Jamf Pro. Deploy macOS Sonoma updates with controlled rollout, testing phases, and user communication strategies.',
                'source': 'Update_macOS_Managed.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Update_macOS_Managed.pdf',
                'page': 1,
                'keywords': ['macos sonoma', 'managed updates', 'jamf pro', 'software updates', 'controlled rollout', 'testing', 'deployment']
            },
            {
                'text': 'Add a Mac Computer to Apple Business Manager or Apple School Manager without erasing it first. Learn non-destructive methods to enroll existing Mac computers into management without losing user data or configurations.',
                'source': 'Add_Mac_ABM_No_Erase.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Add_Mac_ABM_No_Erase.pdf',
                'page': 1,
                'keywords': ['apple business manager', 'apple school manager', 'mac enrollment', 'no erase', 'non-destructive', 'device management']
            },
            {
                'text': 'Restore a Deleted Configuration Profile in Jamf Pro. Recover accidentally deleted configuration profiles, policies, and other Jamf Pro objects using built-in recovery and backup features.',
                'source': 'Restore_Deleted_Objects.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Restore_Deleted_Objects.pdf',
                'page': 1,
                'keywords': ['restore', 'deleted', 'configuration profile', 'jamf pro', 'recovery', 'backup', 'objects']
            },
            {
                'text': 'Create a Jamf Smart Group for the Current Version of macOS. Set up dynamic smart groups that automatically identify devices running the latest macOS version for patching and compliance purposes.',
                'source': 'Jamf_Smart_Group_Patch.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Jamf_Smart_Group_Patch.pdf',
                'page': 1,
                'keywords': ['jamf smart group', 'macos version', 'patch management', 'compliance', 'dynamic groups', 'current version']
            },
            {
                'text': 'Change the Email Address Associated with an Apple Account. Step-by-step guide for updating Apple ID email addresses while maintaining account access and device associations.',
                'source': 'Change_Email_Address_Apple_Account.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Change_Email_Address_Apple_Account.pdf',
                'page': 1,
                'keywords': ['apple account', 'email address', 'apple id', 'account management', 'email change', 'device association']
            },
            {
                'text': 'Configure Sonoma Blocker with Jamf Pro to prevent unwanted macOS upgrades. Set up policies and restrictions to control when and how users can upgrade to macOS Sonoma.',
                'source': 'Sonoma_Blocker.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Sonoma_Blocker.pdf',
                'page': 1,
                'keywords': ['sonoma blocker', 'macos upgrade', 'jamf pro', 'upgrade prevention', 'policies', 'restrictions']
            },
            {
                'text': 'Use Profiles in Web Browsers for enhanced security and user management. Configure browser profiles, security settings, and user preferences across different web browsers.',
                'source': 'Web_Browsers_Profiles.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Web_Browsers_Profiles.pdf',
                'page': 1,
                'keywords': ['web browser', 'profiles', 'browser security', 'user management', 'browser settings', 'preferences']
            },
            {
                'text': 'Configure SMTP Server Integration with Microsoft 365 Per App Password in Jamf Pro. Set up secure email integration using Microsoft 365 app-specific passwords for enhanced security.',
                'source': 'App_Password_Jamf.pdf',
                'url': 'https://hcsonline.com/images/PDFs/App_Password_Jamf.pdf',
                'page': 1,
                'keywords': ['smtp server', 'microsoft 365', 'app password', 'jamf pro', 'email integration', 'security', 'authentication']
            },
            {
                'text': 'Upgrade macOS using erase-install and Jamf Pro for clean system installations. Perform comprehensive macOS upgrades with disk erasure for optimal performance and security.',
                'source': 'erase-install.pdf',
                'url': 'https://hcsonline.com/images/PDFs/erase-install.pdf',
                'page': 1,
                'keywords': ['macos upgrade', 'erase-install', 'jamf pro', 'clean installation', 'disk erase', 'system upgrade']
            },
            {
                'text': 'Configure Account Driven Enrollment and Enroll a Personal Device in Jamf Pro. Set up user-initiated enrollment for personal devices while maintaining security and compliance standards.',
                'source': 'Jamf_Account_Driven.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Jamf_Account_Driven.pdf',
                'page': 1,
                'keywords': ['account driven enrollment', 'personal device', 'jamf pro', 'user enrollment', 'byod', 'device enrollment']
            },
            {
                'text': 'A Guide to Installing and Using Pantone Connect in Adobe Creative Cloud. Comprehensive setup and usage instructions for Pantone color management integration with Adobe Creative Suite applications.',
                'source': 'Adobe_Pantone.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Adobe_Pantone.pdf',
                'page': 1,
                'keywords': ['pantone connect', 'adobe creative cloud', 'color management', 'creative suite', 'design tools', 'pantone colors']
            },
            {
                'text': 'Introduction to Shell Scripting Using Zsh. Learn fundamental shell scripting concepts, syntax, and best practices using the Z shell (Zsh) for macOS automation and system administration.',
                'source': 'Scripting_Intro_Zsh.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Scripting_Intro_Zsh.pdf',
                'page': 1,
                'keywords': ['shell scripting', 'zsh', 'automation', 'system administration', 'macos scripting', 'command line']
            },
            {
                'text': 'Configure Escrow Buddy to Escrow a FileVault Personal Recovery Key (PRK) in Jamf Pro. Set up secure FileVault key management and recovery processes for enterprise Mac security.',
                'source': 'Jamf_Escrow_Buddy.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Jamf_Escrow_Buddy.pdf',
                'page': 1,
                'keywords': ['escrow buddy', 'filevault', 'personal recovery key', 'jamf pro', 'disk encryption', 'key management', 'security']
            },
            {
                'text': 'Use Jamf Pro to Deploy iOS Apps to Mac with Apple Silicon. Deploy iPhone and iPad applications on Apple Silicon Mac computers using Jamf Pro management and distribution policies.',
                'source': 'Jamf_Pro_to_Mac_Silicon.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Jamf_Pro_to_Mac_Silicon.pdf',
                'page': 1,
                'keywords': ['jamf pro', 'ios apps', 'apple silicon', 'mac deployment', 'app distribution', 'mobile apps', 'silicon macs']
            },
            {
                'text': 'Setup a Federated Connection to Apple Business Manager for seamless directory integration. Configure federated identity management to sync users and groups between your organization and Apple Business Manager.',
                'source': 'ABM_Federation.pdf',
                'url': 'https://hcsonline.com/images/PDFs/ABM_Federation.pdf',
                'page': 1,
                'keywords': ['apple business manager', 'federation', 'directory integration', 'identity management', 'user sync', 'federated connection']
            },
            {
                'text': 'Setup and Use 1Password for Two-Factor Authentication. Implement secure two-factor authentication workflows using 1Password for enhanced account security and password management.',
                'source': '2FA_1Password.pdf',
                'url': 'https://hcsonline.com/images/PDFs/2FA_1Password.pdf',
                'page': 1,
                'keywords': ['1password', 'two-factor authentication', '2fa', 'password management', 'security', 'authentication']
            },
            {
                'text': 'Configure Local Administrator Password Solution (LAPS) in Jamf Pro. Implement automated local administrator password management for enhanced Mac security and compliance.',
                'source': 'Jamf_LAPS_Configure.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Jamf_LAPS_Configure.pdf',
                'page': 1,
                'keywords': ['laps', 'local administrator password', 'jamf pro', 'password management', 'security', 'compliance', 'admin passwords']
            },
            {
                'text': 'Resolve Managed Apple ID Conflicts for seamless user account management. Troubleshoot and fix common issues with Managed Apple IDs in enterprise and education environments.',
                'source': 'Managed_Apple_IDs.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Managed_Apple_IDs.pdf',
                'page': 1,
                'keywords': ['managed apple id', 'apple id conflicts', 'user account management', 'troubleshooting', 'enterprise', 'education']
            },
            {
                'text': 'Install SentinelOne with Jamf Pro for comprehensive endpoint security. Deploy and configure SentinelOne endpoint detection and response solution across your Mac fleet using Jamf Pro policies.',
                'source': 'Jamf_Install_SentinalOne.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Jamf_Install_SentinalOne.pdf',
                'page': 1,
                'keywords': ['sentinelone', 'endpoint security', 'jamf pro', 'security deployment', 'endpoint protection', 'threat detection']
            },
            {
                'text': 'Configure Security Keys for Apple ID to enhance account security with hardware-based authentication. Set up and manage physical security keys for Apple ID two-factor authentication and account protection.',
                'source': 'Security_Key_Apple_ID.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Security_Key_Apple_ID.pdf',
                'page': 1,
                'keywords': ['security keys', 'apple id', 'hardware authentication', 'two-factor authentication', 'account security', 'physical keys']
            },
            {
                'text': 'Configure Jamf Connect with Google Cloud Identity for seamless enterprise authentication. Set up single sign-on integration between Jamf Connect and Google Cloud Identity services for unified user management.',
                'source': 'JamfGoogleCloud.pdf',
                'url': 'https://hcsonline.com/images/PDFs/JamfGoogleCloud.pdf',
                'page': 1,
                'keywords': ['jamf connect', 'google cloud identity', 'single sign-on', 'enterprise authentication', 'user management', 'cloud integration']
            },
            {
                'text': 'Manage Background Tasks with Jamf Pro for optimized system performance. Configure and monitor background processes, scheduled tasks, and system maintenance operations across your Mac fleet.',
                'source': 'Manage_Background_Tasks_Jamf.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Manage_Background_Tasks_Jamf.pdf',
                'page': 1,
                'keywords': ['background tasks', 'jamf pro', 'system performance', 'scheduled tasks', 'system maintenance', 'mac fleet', 'process management']
            },
            {
                'text': 'Configure Jamf Connect with Okta for enterprise single sign-on authentication. Set up seamless integration between Jamf Connect and Okta identity provider for unified user access management.',
                'source': 'Jamf_Connect_Okta.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Jamf_Connect_Okta.pdf',
                'page': 1,
                'keywords': ['jamf connect', 'okta', 'single sign-on', 'enterprise authentication', 'identity provider', 'user access management', 'sso integration']
            },
            {
                'text': 'Add an Additional Layer of Protection to iPhone and iPad Cellular Data by Enabling a SIM PIN. Enhance mobile device security by configuring SIM PIN protection for cellular data access.',
                'source': 'SIM_PIN.pdf',
                'url': 'https://hcsonline.com/images/PDFs/SIM_PIN.pdf',
                'page': 1,
                'keywords': ['sim pin', 'iphone', 'ipad', 'cellular data', 'mobile security', 'device protection', 'sim card security']
            },
            {
                'text': 'Install TeamViewer Host with Jamf Pro for remote access management. Deploy and configure TeamViewer Host application across your Mac fleet for remote support and system administration.',
                'source': 'Jamf_Teamviewer_Host.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Jamf_Teamviewer_Host.pdf',
                'page': 1,
                'keywords': ['teamviewer host', 'jamf pro', 'remote access', 'remote support', 'system administration', 'mac deployment', 'remote management']
            },
            {
                'text': 'Outlook for iPadOS configuration and optimization. Set up and configure Microsoft Outlook for optimal performance and functionality on iPad devices in enterprise environments.',
                'source': 'Outlook_for_iPadOS.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Outlook_for_iPadOS.pdf',
                'page': 1,
                'keywords': ['outlook', 'ipados', 'ipad', 'microsoft', 'email configuration', 'enterprise', 'mobile productivity']
            },
            {
                'text': 'Open Compressed ZIP Files Saved in OneDrive. Guide for accessing and extracting ZIP archive files stored in Microsoft OneDrive cloud storage across different devices and platforms.',
                'source': 'HCS_ZIP_OneDrive.pdf',
                'url': 'https://hcsonline.com/images/PDFs/HCS_ZIP_OneDrive.pdf',
                'page': 1,
                'keywords': ['zip files', 'onedrive', 'compressed files', 'cloud storage', 'file extraction', 'microsoft', 'archive management']
            },
            {
                'text': 'Auto Configure Microsoft 365 Mail Account with Jamf Pro for streamlined email setup. Automate the configuration of Microsoft 365 email accounts across your Mac and iOS device fleet.',
                'source': 'Auto_Config_O365_Mail.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Auto_Config_O365_Mail.pdf',
                'page': 1,
                'keywords': ['microsoft 365', 'email configuration', 'jamf pro', 'auto configuration', 'mail setup', 'office 365', 'automated deployment']
            },
            {
                'text': 'Deploy Cisco AnyConnect with Jamf Pro for enterprise VPN management. Configure and deploy Cisco AnyConnect VPN client across your Mac fleet for secure remote access and network connectivity.',
                'source': 'Deploying_Cisco_AnyConnect.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Deploying_Cisco_AnyConnect.pdf',
                'page': 1,
                'keywords': ['cisco anyconnect', 'vpn deployment', 'jamf pro', 'remote access', 'network security', 'enterprise vpn', 'secure connectivity']
            },
            {
                'text': 'Initiate a sysdiagnose on your Apple Devices for comprehensive system diagnostics. Generate detailed system diagnostic reports for troubleshooting Mac, iPhone, and iPad issues.',
                'source': 'Sysdiagnose.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Sysdiagnose.pdf',
                'page': 1,
                'keywords': ['sysdiagnose', 'system diagnostics', 'apple devices', 'troubleshooting', 'diagnostic reports', 'system analysis', 'technical support']
            },
            {
                'text': 'Deploy ESET with Jamf Pro for comprehensive endpoint security. Install and configure ESET antivirus and security solutions across your Mac fleet using Jamf Pro policies and management.',
                'source': 'Jamf_ESET.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Jamf_ESET.pdf',
                'page': 1,
                'keywords': ['eset', 'antivirus', 'jamf pro', 'endpoint security', 'malware protection', 'security deployment', 'threat protection']
            },
            {
                'text': 'Integrate TeamViewer into Jamf Pro for enhanced remote support capabilities. Set up comprehensive TeamViewer integration with Jamf Pro for streamlined remote access and technical support workflows.',
                'source': 'Teamviewer_Jamf_Integration.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Teamviewer_Jamf_Integration.pdf',
                'page': 1,
                'keywords': ['teamviewer integration', 'jamf pro', 'remote support', 'technical support', 'remote access', 'support workflows', 'integration']
            },
            {
                'text': 'Upgrade to macOS Big Sur using Self Service with Jamf Pro. Deploy macOS Big Sur upgrades through Self Service portal, giving users controlled access to major OS updates.',
                'source': 'macOS_Big_Sur_Self_Service.pdf',
                'url': 'https://hcsonline.com/images/PDFs/macOS_Big_Sur_Self_Service.pdf',
                'page': 1,
                'keywords': ['macos big sur', 'self service', 'jamf pro', 'os upgrade', 'user portal', 'controlled updates', 'major updates']
            },
            {
                'text': 'Create a "Never-Run" VM Snapshot with VMware Fusion Player for testing Automated Device Enrollment. Set up virtual machine environments for ADE testing without affecting production systems.',
                'source': 'Never_Run_VM_Fusion_Automation.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Never_Run_VM_Fusion_Automation.pdf',
                'page': 1,
                'keywords': ['vmware fusion', 'vm snapshot', 'automated device enrollment', 'ade testing', 'virtual machine', 'testing environment', 'development']
            },
            {
                'text': 'Deploy Splashtop Streamer with Jamf Pro for remote desktop access. Install and configure Splashtop remote desktop solution across your Mac fleet for remote work and support scenarios.',
                'source': 'Deploying_Splashtop_Streamer.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Deploying_Splashtop_Streamer.pdf',
                'page': 1,
                'keywords': ['splashtop streamer', 'remote desktop', 'jamf pro', 'remote access', 'remote work', 'desktop streaming', 'remote support']
            },
            {
                'text': 'Configure Jamf Connect Login, Azure, and IDent for Certificate Provisioning. Set up advanced certificate provisioning workflows integrating Jamf Connect with Azure and IDent for enhanced security.',
                'source': 'Jamf_Azure_IDent_Cert_Provisioning.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Jamf_Azure_IDent_Cert_Provisioning.pdf',
                'page': 1,
                'keywords': ['jamf connect', 'azure', 'ident', 'certificate provisioning', 'advanced security', 'certificate management', 'identity integration']
            },
            {
                'text': 'Managing Apple Devices: macOS commands and queries that require supervision. Comprehensive guide to supervised device management commands, restrictions, and administrative controls for enterprise Apple devices.',
                'source': 'Managing_Apple_Devices.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Managing_Apple_Devices.pdf',
                'page': 1,
                'keywords': ['apple device management', 'macos commands', 'supervision', 'device restrictions', 'administrative controls', 'supervised devices']
            },
            {
                'text': 'Recommendations and Best Practices for Wi-Fi and Apple Devices. Optimize wireless network configuration, security settings, and connectivity for Apple devices in enterprise environments.',
                'source': 'Wi-FI_Apple_Devices.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Wi-FI_Apple_Devices.pdf',
                'page': 1,
                'keywords': ['wifi', 'wireless network', 'apple devices', 'network configuration', 'connectivity', 'network security', 'best practices']
            },
            {
                'text': 'Using Jamf Connect with G Suite Cloud Identity for enterprise authentication. Configure Jamf Connect integration with Google G Suite (now Google Workspace) for seamless user authentication and management.',
                'source': 'Jamf_Connect_GSuite.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Jamf_Connect_GSuite.pdf',
                'page': 1,
                'keywords': ['jamf connect', 'g suite', 'google workspace', 'cloud identity', 'enterprise authentication', 'user management', 'google integration']
            },
            {
                'text': 'Recommendations and Practices for Content Caching with Apple devices. Optimize content delivery, reduce bandwidth usage, and improve performance with Apple Content Caching service configuration.',
                'source': 'Apple_Content_Caching.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Apple_Content_Caching.pdf',
                'page': 1,
                'keywords': ['content caching', 'apple content caching', 'bandwidth optimization', 'content delivery', 'network performance', 'caching service']
            },
            {
                'text': 'Deploy SplashBuddy as a PreStage Enrollment Package in Jamf Pro. Enhance user onboarding experience with customized splash screens and guided setup during device enrollment processes.',
                'source': 'Jamf_Splashbuddy.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Jamf_Splashbuddy.pdf',
                'page': 1,
                'keywords': ['splashbuddy', 'prestage enrollment', 'jamf pro', 'user onboarding', 'device enrollment', 'setup experience', 'guided setup']
            },
            {
                'text': 'Deploy Zoom Through Addigy with Privacy Preferences Policy Control. Configure Zoom deployment using Addigy MDM with proper privacy settings and policy controls for enterprise compliance.',
                'source': 'Addigy_Deploying_Zoom.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Addigy_Deploying_Zoom.pdf',
                'page': 1,
                'keywords': ['addigy', 'zoom deployment', 'privacy preferences', 'policy control', 'mdm deployment', 'enterprise compliance', 'video conferencing']
            },
            {
                'text': 'Deploy Microsoft 365 Apps and Books Through Addigy. Configure and deploy Microsoft Office applications and educational content through Addigy MDM platform for comprehensive productivity suite management.',
                'source': 'Addigy_Microsoft365.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Addigy_Microsoft365.pdf',
                'page': 1,
                'keywords': ['addigy', 'microsoft 365', 'office apps', 'educational content', 'mdm deployment', 'productivity suite', 'app management']
            },
            {
                'text': 'Create a Managed Apple ID for APNS in Apple Business Manager/Apple School Manager. Set up Managed Apple IDs specifically for Apple Push Notification Service integration and enterprise device management.',
                'source': 'MAID_APNS_user.pdf',
                'url': 'https://hcsonline.com/images/PDFs/MAID_APNS_user.pdf',
                'page': 1,
                'keywords': ['managed apple id', 'apns', 'apple push notifications', 'apple business manager', 'apple school manager', 'device management', 'notification service']
            },
            {
                'text': 'Creating Blueprints and Provisioning Workflows with Apple Configurator 2. Master advanced Apple Configurator 2 techniques for creating device blueprints, provisioning workflows, and automated device deployment strategies.',
                'source': 'Apple_Configurator_2_Blueprints.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Apple_Configurator_2_Blueprints.pdf',
                'page': 1,
                'keywords': ['apple configurator 2', 'device blueprints', 'provisioning workflows', 'device deployment', 'automation', 'device configuration']
            },
            {
                'text': 'Integrate and Configure Jamf Pro and Microsoft Intune for Conditional Access for macOS. Set up comprehensive conditional access policies integrating Jamf Pro compliance with Microsoft Intune security requirements.',
                'source': 'Jamf_Pro_Intune.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Jamf_Pro_Intune.pdf',
                'page': 1,
                'keywords': ['jamf pro', 'microsoft intune', 'conditional access', 'macos', 'compliance integration', 'security policies', 'enterprise security']
            },
            {
                'text': 'Add Apple TV to Apple Business Manager for Automated Device Enrollment in Jamf Pro. Configure Apple TV devices for automated enrollment and management through Apple Business Manager and Jamf Pro integration.',
                'source': 'How_to_add_ATV_to_ABM.pdf',
                'url': 'https://hcsonline.com/images/PDFs/How_to_add_ATV_to_ABM.pdf',
                'page': 1,
                'keywords': ['apple tv', 'apple business manager', 'automated device enrollment', 'jamf pro', 'atv management', 'device enrollment', 'apple tv configuration']
            },
            {
                'text': 'Enrolling Your Organization in Apple Business Manager/Apple School Manager. Complete guide to organizational enrollment processes, setup requirements, and administrative configuration for Apple Business Manager and Apple School Manager.',
                'source': 'Enroll_Organization_ABM_ASM.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Enroll_Organization_ABM_ASM.pdf',
                'page': 1,
                'keywords': ['apple business manager', 'apple school manager', 'organization enrollment', 'setup requirements', 'administrative configuration', 'institutional setup']
            },
            {
                'text': 'Configure Chrome Browser Cloud Management in Jamf Pro. Deploy and manage Google Chrome browser with cloud management capabilities through Jamf Pro policies and configuration profiles.',
                'source': 'Chrome_Cloud_Management_Jamf.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Chrome_Cloud_Management_Jamf.pdf',
                'page': 1,
                'keywords': ['chrome browser', 'cloud management', 'jamf pro', 'google chrome', 'browser management', 'web browser policies', 'chrome deployment']
            },
            {
                'text': 'Integrate Jamf Pro with Google Secure LDAP as a Cloud Identity Provider. Configure secure LDAP integration between Jamf Pro and Google Cloud Identity for enterprise authentication and directory services.',
                'source': 'Jamf_Google_Secure_LDAP.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Jamf_Google_Secure_LDAP.pdf',
                'page': 1,
                'keywords': ['jamf pro', 'google secure ldap', 'cloud identity provider', 'enterprise authentication', 'directory services', 'ldap integration', 'google cloud']
            },
            {
                'text': 'Send Jamf Notifications to Slack for enhanced team communication. Configure automated Jamf Pro notifications and alerts to be delivered to Slack channels for real-time monitoring and incident response.',
                'source': 'Jamf_Slack_Notifications.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Jamf_Slack_Notifications.pdf',
                'page': 1,
                'keywords': ['jamf notifications', 'slack integration', 'team communication', 'automated alerts', 'monitoring', 'incident response', 'collaboration tools']
            },
            {
                'text': 'Upgrade to macOS Catalina using Self Service with Jamf Pro. Deploy macOS Catalina upgrades through Self Service portal, providing users with controlled access to major operating system updates.',
                'source': 'macOS_Catalina_Self_Service.pdf',
                'url': 'https://hcsonline.com/images/PDFs/macOS_Catalina_Self_Service.pdf',
                'page': 1,
                'keywords': ['macos catalina', 'self service', 'jamf pro', 'os upgrade', 'user portal', 'controlled updates', 'operating system deployment']
            },
            {
                'text': 'Verify Your Domain for Apple Business Manager or Apple School Manager. Complete domain verification process, DNS configuration, and organizational validation requirements for Apple Business Manager and Apple School Manager enrollment.',
                'source': 'ABMASM_Verification.pdf',
                'url': 'https://hcsonline.com/images/PDFs/ABMASM_Verification.pdf',
                'page': 1,
                'keywords': ['domain verification', 'apple business manager', 'apple school manager', 'dns configuration', 'organizational validation', 'enrollment requirements', 'domain setup']
            },
            {
                'text': 'How to Use a Google Account with an App Password for a SMTP relay in Jamf Pro. Configure secure email relay using Google Workspace app passwords for Jamf Pro notifications, reports, and communication features.',
                'source': 'Jamf_Google_App_Password.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Jamf_Google_App_Password.pdf',
                'page': 1,
                'keywords': ['google app password', 'smtp relay', 'jamf pro', 'email configuration', 'google workspace', 'secure email', 'notifications']
            },
            {
                'text': 'A Guide for Configuring the macOS Catalina Kerberos Single Sign-On Extension. Set up Kerberos-based authentication for seamless single sign-on experience on macOS Catalina systems.',
                'source': 'Jamf_Kerberos.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Jamf_Kerberos.pdf',
                'page': 1,
                'keywords': ['kerberos', 'single sign-on', 'macos catalina', 'authentication', 'sso extension', 'network authentication', 'identity management']
            },
            {
                'text': 'Best Practices for Managing your Apple ID. Comprehensive guide for Apple ID management, security settings, account recovery, and best practices for personal and enterprise use.',
                'source': 'Managing_Your_Apple_ID_HCS.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Managing_Your_Apple_ID_HCS.pdf',
                'page': 1,
                'keywords': ['apple id management', 'best practices', 'account security', 'apple id', 'account recovery', 'security settings', 'enterprise apple id']
            },
            {
                'text': 'A Guide to Configuring macOS Catalina Bootstrap Token Using Jamf. Configure bootstrap tokens for secure system administration and credential management on macOS Catalina systems.',
                'source': 'Bootstrap_Token_Guide.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Bootstrap_Token_Guide.pdf',
                'page': 1,
                'keywords': ['bootstrap token', 'macos catalina', 'jamf pro', 'secure token', 'system administration', 'credential management', 'security']
            },
            {
                'text': 'How to use Jamf Helper in Jamf Pro. Learn to create custom user dialogs, notifications, and interactive prompts using Jamf Helper for enhanced user experience and communication.',
                'source': 'How_to_use_Jamf_Helper.pdf',
                'url': 'https://hcsonline.com/images/PDFs/How_to_use_Jamf_Helper.pdf',
                'page': 1,
                'keywords': ['jamf helper', 'user dialogs', 'notifications', 'interactive prompts', 'user experience', 'jamf pro', 'communication']
            },
            {
                'text': 'How to Set the Default Application Program Using Self Service. Guide users through setting default applications for file types using Jamf Pro Self Service portal for improved productivity.',
                'source': 'Set_Default_App_SS.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Set_Default_App_SS.pdf',
                'page': 1,
                'keywords': ['default applications', 'self service', 'jamf pro', 'file associations', 'user portal', 'productivity', 'application settings']
            },
            {
                'text': 'How to Deploy DEPNotify as a Jamf Pro PreStage Enrollment Package with Custom Launching Scripts. Create engaging enrollment experiences with DEPNotify customization and automated setup workflows.',
                'source': 'Signed_DEPNotify.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Signed_DEPNotify.pdf',
                'page': 1,
                'keywords': ['depnotify', 'prestage enrollment', 'jamf pro', 'enrollment experience', 'custom scripts', 'automated setup', 'device onboarding']
            },
            {
                'text': 'Deploying and Configuring Enterprise Connect. Set up Enterprise Connect for seamless network authentication and secure access to corporate resources on macOS systems.',
                'source': 'Enterprise_Connect.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Enterprise_Connect.pdf',
                'page': 1,
                'keywords': ['enterprise connect', 'network authentication', 'corporate resources', 'macos', 'secure access', 'enterprise security', 'authentication']
            },
            {
                'text': 'Creating a Virtual Machine for Automated Device Enrollment. Set up virtual machines for testing Automated Device Enrollment (ADE) workflows, device provisioning, and enrollment scenarios.',
                'source': 'Creating_VM.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Creating_VM.pdf',
                'page': 1,
                'keywords': ['virtual machine', 'automated device enrollment', 'ade testing', 'device provisioning', 'enrollment testing', 'vm setup', 'testing environment']
            },
            {
                'text': 'How to Upload Packages to Jamf Cloud using Autopkgr. Streamline package management by automating package uploads to Jamf Cloud using AutoPkgr for efficient software distribution.',
                'source': 'Jamf_Autopkgr.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Jamf_Autopkgr.pdf',
                'page': 1,
                'keywords': ['autopkgr', 'jamf cloud', 'package upload', 'software distribution', 'automation', 'package management', 'app deployment']
            },
            {
                'text': 'A Guide to Integrate Azure Active Directory with Jamf Pro. Complete integration guide for connecting Azure Active Directory with Jamf Pro for unified identity management and authentication.',
                'source': 'Jamf_Microsoft_Azure_Integration.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Jamf_Microsoft_Azure_Integration.pdf',
                'page': 1,
                'keywords': ['azure active directory', 'jamf pro integration', 'identity management', 'microsoft azure', 'enterprise authentication', 'directory services', 'sso integration']
            },
            {
                'text': 'Creating a Jamf Pro Cloud Distribution Point with Amazon Web Services. Set up AWS-based distribution points for Jamf Pro to improve content delivery and reduce bandwidth usage.',
                'source': 'Jamf_Cloud_Distribution_AWS.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Jamf_Cloud_Distribution_AWS.pdf',
                'page': 1,
                'keywords': ['jamf distribution point', 'amazon web services', 'aws', 'cloud storage', 'content delivery', 'bandwidth optimization', 'jamf infrastructure']
            },
            {
                'text': 'Using Open SSL to generate CSR and getting a signed Certificate. Create Certificate Signing Requests and obtain signed certificates for secure Jamf Pro communications and SSL/TLS implementation.',
                'source': 'Jamf_OpenSSL_CSR.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Jamf_OpenSSL_CSR.pdf',
                'page': 1,
                'keywords': ['openssl', 'certificate signing request', 'csr', 'ssl certificate', 'jamf security', 'tls', 'certificate management']
            },
            {
                'text': 'Installing Jamf Infrastructure Manager on a Windows Server. Deploy Jamf Infrastructure Manager on Windows Server for enhanced network performance and distributed content delivery.',
                'source': 'Jamf_Infrstructure_Manager.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Jamf_Infrstructure_Manager.pdf',
                'page': 1,
                'keywords': ['jamf infrastructure manager', 'windows server', 'network performance', 'distributed content', 'jimf deployment', 'server installation', 'infrastructure']
            },
            {
                'text': 'Wireless Network Design with Apple Devices. Design and optimize wireless networks for Apple device environments, including WiFi best practices, performance optimization, and security considerations.',
                'source': 'Wireless_Network_Apple.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Wireless_Network_Apple.pdf',
                'page': 1,
                'keywords': ['wireless network design', 'apple devices', 'wifi optimization', 'network performance', 'wireless security', 'network planning', 'wifi best practices']
            },
            {
                'text': 'macOS Sequoia: A Guide to Your System Settings. Comprehensive guide to navigating and configuring macOS Sequoia system settings, preferences, and advanced configuration options.',
                'source': 'System_Settings_Sequoia.pdf',
                'url': 'https://hcsonline.com/images/PDFs/System_Settings_Sequoia.pdf',
                'page': 1,
                'keywords': ['macos sequoia', 'system settings', 'system preferences', 'sequoia configuration', 'macos setup', 'system configuration', 'sequoia guide']
            },
            {
                'text': 'A Guide to iPadOS 18. Complete user guide for iPadOS 18 features, new capabilities, user interface changes, and productivity enhancements for iPad users.',
                'source': 'Guide_iPadOS_18.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Guide_iPadOS_18.pdf',
                'page': 1,
                'keywords': ['ipados 18', 'ipad guide', 'ipados features', 'ipad productivity', 'ios 18', 'ipad user guide', 'mobile productivity']
            },
            {
                'text': 'macOS Ventura: A Guide to Your System Settings. Navigate and configure macOS Ventura system settings, understand new interface changes, and optimize system preferences.',
                'source': 'System_Settings_Ventura.pdf',
                'url': 'https://hcsonline.com/images/PDFs/System_Settings_Ventura.pdf',
                'page': 1,
                'keywords': ['macos ventura', 'system settings', 'ventura configuration', 'system preferences', 'macos setup', 'ventura guide', 'system configuration']
            },
            {
                'text': 'Getting Started with macOS Ventura. Introduction to macOS Ventura features, installation guide, setup procedures, and essential getting started information for new users.',
                'source': 'macOS_Ventura_Getting_Started.pdf',
                'url': 'https://hcsonline.com/images/PDFs/macOS_Ventura_Getting_Started.pdf',
                'page': 1,
                'keywords': ['macos ventura', 'getting started', 'ventura setup', 'macos installation', 'ventura introduction', 'new user guide', 'ventura basics']
            },
            {
                'text': 'macOS Sonoma: A Guide to Your System Settings. Complete guide to macOS Sonoma system settings, configuration options, privacy controls, and system preference management.',
                'source': 'System_Settings_Sonoma.pdf',
                'url': 'https://hcsonline.com/images/PDFs/System_Settings_Sonoma.pdf',
                'page': 1,
                'keywords': ['macos sonoma', 'system settings', 'sonoma configuration', 'system preferences', 'sonoma setup', 'system configuration', 'privacy settings']
            },
            {
                'text': 'Getting Started with macOS Sonoma. Essential guide for new macOS Sonoma users covering installation, setup, key features, and initial configuration steps.',
                'source': 'Getting_Started_Sonoma.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Getting_Started_Sonoma.pdf',
                'page': 1,
                'keywords': ['macos sonoma', 'getting started', 'sonoma setup', 'sonoma installation', 'sonoma guide', 'new user', 'sonoma basics']
            },
            {
                'text': 'A Guide to iPadOS 17. Comprehensive user guide for iPadOS 17 covering new features, interface updates, productivity tools, and enhanced iPad capabilities.',
                'source': 'Guide_to_iPadOS_17.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Guide_to_iPadOS_17.pdf',
                'page': 1,
                'keywords': ['ipados 17', 'ipad guide', 'ipados features', 'ipad productivity', 'ios 17', 'ipad user guide', 'mobile features']
            },
            {
                'text': 'Microsoft Outlook for Mac User Guide. Complete guide to using Microsoft Outlook on Mac, including email management, calendar integration, and productivity features.',
                'source': 'Outlook_365_for_Mac.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Outlook_365_for_Mac.pdf',
                'page': 1,
                'keywords': ['microsoft outlook', 'outlook mac', 'email management', 'microsoft 365', 'outlook guide', 'mac email', 'office 365']
            },
            {
                'text': 'Microsoft Outlook for iPadOS. User guide for Microsoft Outlook on iPad, covering email, calendar, and productivity features optimized for iPad interface.',
                'source': 'Outlook_for_iPadOS.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Outlook_for_iPadOS.pdf',
                'page': 1,
                'keywords': ['microsoft outlook', 'outlook ipad', 'ipados email', 'outlook mobile', 'ipad productivity', 'mobile email', 'office 365 ipad']
            },
            {
                'text': 'Microsoft Outlook for iOS - iPhone. Complete guide to using Microsoft Outlook on iPhone, including mobile email management, calendar sync, and iPhone-specific features.',
                'source': 'Outlook_for_iOS_iPhone_2022.pdf',
                'url': 'https://hcsonline.com/images/PDFs/Outlook_for_iOS_iPhone_2022.pdf',
                'page': 1,
                'keywords': ['microsoft outlook', 'outlook iphone', 'ios email', 'mobile outlook', 'iphone email', 'outlook mobile', 'ios productivity']
            }
        ]
        
        # Improved keyword matching with intent recognition
        relevant = []
        
        for chunk in knowledge_chunks:
            relevance_score = 0
            
            # Base keyword matching
            for keyword in chunk['keywords']:
                if keyword in query_lower:
                    relevance_score += 0.3
            
            # Boost score for intent-specific matches
            chunk_text_lower = chunk['text'].lower()
            chunk_keywords_text = ' '.join(chunk['keywords']).lower()
            
            # Installation intent boost
            if install_intent and any(word in chunk_text_lower or word in chunk_keywords_text for word in ['install', 'deploy', 'setup', 'configure']):
                relevance_score += 0.5
            
            # Troubleshooting intent boost  
            if troubleshoot_intent and any(word in chunk_text_lower or word in chunk_keywords_text for word in ['troubleshoot', 'fix', 'error', 'issue']):
                relevance_score += 0.5
            
            # Configuration intent boost
            if config_intent and any(word in chunk_text_lower or word in chunk_keywords_text for word in ['configure', 'config', 'settings']):
                relevance_score += 0.4
            
            # Exact phrase matching gets highest boost
            key_phrases = []
            if 'jamf connect' in query_lower:
                key_phrases.append('jamf connect')
            if 'jamf pro' in query_lower:
                key_phrases.append('jamf pro')
            if 'apple configurator' in query_lower:
                key_phrases.append('apple configurator')
            
            for phrase in key_phrases:
                if phrase in chunk_text_lower or phrase in chunk_keywords_text:
                    relevance_score += 0.7
            
            # Only include chunks with reasonable relevance
            if relevance_score > 0.2:
                chunk['relevance_score'] = min(relevance_score, 1.0)
                relevant.append(chunk)
        
        # Sort by relevance score
        relevant.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # If no good matches, provide clarifying questions instead
        if not relevant or (relevant and relevant[0]['relevance_score'] < 0.5):
            return self.get_clarifying_results(query_lower, knowledge_chunks[:3])
        
        return relevant[:max_results]
    
    def get_clarifying_results(self, query_lower: str, fallback_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return clarifying questions when search results are unclear"""
        clarifying_chunk = {
            'text': f'''I want to make sure I give you the most relevant information. Your question "{query_lower}" could refer to several different topics. Please clarify:

**Are you looking for:**
1. **Installation instructions** - How to deploy and install software/packages
2. **Configuration guidance** - How to set up and configure settings
3. **Troubleshooting help** - How to fix issues and problems
4. **General information** - Overview and background information

Please ask a more specific question like:
- "How do I **install** Jamf Connect on macOS?"
- "How do I **configure** Jamf Connect settings?"
- "How do I **troubleshoot** Jamf Connect login issues?"

This will help me find the exact documentation you need from our comprehensive knowledge base.''',
            'source': 'Clarification_Needed.pdf',
            'url': '',
            'page': 1,
            'keywords': ['clarification', 'help', 'guidance'],
            'relevance_score': 1.0
        }
        return [clarifying_chunk]
    
    def get_follow_up_questions(self, query: str, context_chunks: List[Dict[str, Any]]) -> List[str]:
        """Generate intelligent follow-up questions based on the topic"""
        query_lower = query.lower()
        
        # Topic-specific follow-up questions
        if any(keyword in query_lower for keyword in ['jamf connect', 'sso', 'login']):
            return [
                "How do I troubleshoot Jamf Connect login issues?",
                "What are the Azure AD prerequisites for Jamf Connect?", 
                "How do I configure password synchronization?"
            ]
        elif any(keyword in query_lower for keyword in ['apple configurator', 'device deployment']):
            return [
                "What devices are compatible with Apple Configurator 2?",
                "How do I create device supervision profiles?",
                "What's the difference between USB and wireless deployment?"
            ]
        elif any(keyword in query_lower for keyword in ['jamf pro', 'device management']):
            return [
                "How do I create smart groups in Jamf Pro?",
                "What are best practices for configuration profiles?",
                "How do I set up automated device enrollment?"
            ]
        elif any(keyword in query_lower for keyword in ['sonoma', 'sequoia', 'macos']):
            return [
                "What are the compatibility requirements for this macOS version?",
                "How do I prepare for a fleet-wide macOS upgrade?",
                "What new management features are available?"
            ]
        elif any(keyword in query_lower for keyword in ['zoom', 'teams', 'office', 'microsoft']):
            return [
                "How do I configure app-specific settings?",
                "What are the licensing considerations?",
                "How do I handle app updates and patches?"
            ]
        else:
            # General follow-up questions
            return [
                "What documentation would be most helpful for your specific use case?",
                "Are you looking for step-by-step deployment guides?",
                "Do you need troubleshooting assistance with any specific issues?"
            ]
    
    def generate_response(self, query: str, context_chunks: List[Dict[str, Any]]) -> str:
        """Generate AI response using context chunks"""
        try:
            context = "\n\n".join([f"**Source:** {chunk['source']} (Page {chunk['page']})\n**URL:** {chunk.get('url', '')}\n**Content:** {chunk['text']}" 
                                 for chunk in context_chunks])
            
            system_prompt = """You are the HCS Apple Technology Assistant, an expert in Apple device management following the Apple Style Guide.

CRITICAL INSTRUCTIONS:
1. **VALIDATE RELEVANCE FIRST** - Before answering, check if the provided documentation actually answers the user's question
2. **RECOGNIZE USER INTENT** - Distinguish between:
   - Installation/Deployment questions ("install", "deploy", "setup")  
   - Configuration questions ("configure", "settings", "how to set up")
   - Troubleshooting questions ("fix", "error", "not working", "issue")
   - General information questions ("what is", "explain", "overview")

3. **IF DOCUMENTATION DOESN'T MATCH THE QUESTION:**
   - Say "I want to provide the most relevant information for your question"
   - Ask clarifying questions like: "Are you looking for installation steps, configuration guidance, or troubleshooting help?"
   - Suggest more specific phrasing: "Please ask: 'How do I **install** [software] on macOS?'"

4. **ALWAYS cite specific PDFs and page numbers** when providing information (e.g., "According to Jamf_Connect_Azure.pdf (Page 23)...")
5. **Use rich Markdown formatting** - headers (##), bold (**text**), lists, code blocks
6. **Follow Apple Style Guide terminology**: 
   - Use "sign-in" not "login"
   - Use "System Settings" not "System Preferences" for macOS Ventura and later
   - Use "user" not "end user"
   - Use "app" not "application" 
   - Use "macOS" not "Mac OS" or "OS X"
7. **Link to specific pages** - Include [View PDF: Page X] references
8. **Be specific and actionable** - Provide step-by-step instructions from the documentation
9. **Professional tone** - Clear, concise, authoritative like Apple documentation

EXAMPLE OF GOOD INTENT MATCHING:
- User asks: "How do I install Jamf Connect on macOS?"
- Documentation about: Jamf Connect installation → PERFECT MATCH
- Documentation about: Jamf Connect SSO configuration → ASK FOR CLARIFICATION"""
            
            # This will be handled by the AI prompt directly

            user_prompt = f"""Documentation Context with Page References:
{context}

User Question: {query}

STEP 1: RELEVANCE CHECK
First, analyze if the provided documentation actually answers the user's specific question and intent:
- Does the documentation match what they're asking for?
- Are they asking about installation but documentation shows configuration?  
- Are they asking about troubleshooting but documentation shows setup?

STEP 2: RESPONSE STRATEGY
IF DOCUMENTATION MATCHES USER INTENT:
- Provide comprehensive answer with specific citations
- Use the format below

IF DOCUMENTATION DOESN'T MATCH USER INTENT:
- Say: "I want to provide the most relevant information for your question about [topic]."
- Ask: "Are you looking for: 1) Installation steps 2) Configuration guidance 3) Troubleshooting help?"
- Suggest: "Please ask a more specific question like 'How do I **install** [software]?'"

RESPONSE REQUIREMENTS (when documentation matches):
1. Start with a direct answer citing the specific PDF and page number
2. Use Markdown formatting with ## headers, **bold**, and bullet points
3. Include step-by-step instructions if applicable
4. Add inline citations like: "As detailed in **Jamf_Pro_Guide.pdf** (Page 42)..."
5. End with 2-3 relevant follow-up questions in a "### Related Questions" section
6. Use Apple Style Guide terminology throughout
7. Format any terminal commands in code blocks using ```bash

Provide a comprehensive, well-formatted response that directly references the documentation pages."""

            if self.openai_client:
                try:
                    logger.info("Making OpenAI API call")
                    response = self.openai_client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        max_completion_tokens=1500,
                        temperature=0.7
                    )
                    logger.info("OpenAI API call successful")
                    return response.choices[0].message.content
                except Exception as e:
                    logger.error(f"OpenAI API error: {e}")
            else:
                logger.warning("OpenAI client not available, using fallback")
            
            # Fallback response with follow-up questions and markdown formatting
            topic_questions = self.get_follow_up_questions(query, context_chunks)
            
            # Format sources with proper markdown
            sources_text = ""
            if context_chunks:
                sources_text = "\n\n## 📚 Relevant Documentation:\n"
                for chunk in context_chunks[:3]:
                    sources_text += f"- **{chunk['source']}** (Page {chunk['page']})\n"
            
            follow_up_text = ""
            if topic_questions:
                follow_up_text = f"\n\n### 🤔 Related Questions:\n" + "\n".join([f"- {q}" for q in topic_questions])
            
            # Extract key information from first chunk
            first_chunk = context_chunks[0] if context_chunks else {}
            
            return f"""## Answer from HCS Apple Technology Documentation

Based on **{first_chunk.get('source', 'HCS Documentation')}** (Page {first_chunk.get('page', '1')}):

{first_chunk.get('text', 'I can help you with Apple device management, Jamf Pro configuration, and iOS deployment questions.')[:500]}

{sources_text}

*For detailed information, please refer to the documentation linked above.*{follow_up_text}"""
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I apologize, but I encountered an error generating a response. Please try again."
    
    def chat(self, query: str) -> Dict[str, Any]:
        """Main chat function"""
        if not self.initialized:
            self.initialize()
        
        try:
            relevant_chunks = self.search_knowledge_base(query)
            answer = self.generate_response(query, relevant_chunks)
            
            sources = [
                {
                    'filename': chunk['source'],
                    'page': chunk['page'], 
                    'page_number': chunk['page'],
                    'url': chunk.get('url', f"https://hcsonline.com/images/PDFs/{chunk['source']}"),
                    'relevance_score': chunk.get('relevance_score', 0.0)
                }
                for chunk in relevant_chunks
            ]
            
            return {'answer': answer, 'sources': sources}
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return {
                'answer': 'I apologize, but I encountered an error processing your question. Please try again.',
                'sources': []
            }

# Initialize chat service (lazy initialization for Vercel serverless)
chat_service = ChatService()

def ensure_initialized():
    """Lazy initialization to avoid Vercel serverless timeout"""
    if not chat_service.initialized:
        logger.info("Performing lazy initialization...")
        chat_service.initialize()

@app.route('/api/health')
def health():
    """Health check endpoint - initializes on first call"""
    ensure_initialized()
    doc_chunks = 0
    if RAG_AVAILABLE and chat_service.rag_initialized:
        try:
            doc_chunks = len(rag_system.document_chunks)
        except:
            doc_chunks = 0
    return jsonify({
        "status": "healthy",
        "message": "HCS Apple Technology Assistant API is running",
        "initialized": chat_service.initialized,
        "rag_initialized": chat_service.rag_initialized,
        "rag_available": RAG_AVAILABLE,
        "openai_client_available": chat_service.openai_client is not None,
        "openai_api_key_set": os.getenv('OPENAI_API_KEY') is not None,
        "document_chunks": doc_chunks
    })

@app.route('/api/test-openai')
def test_openai():
    """Test OpenAI API directly"""
    debug_info = {
        "openai_installed": True,
        "api_key_present": os.getenv('OPENAI_API_KEY') is not None,
        "api_key_length": len(os.getenv('OPENAI_API_KEY', '')),
        "client_available": chat_service.openai_client is not None,
        "initialized": chat_service.initialized
    }

    # Try to create OpenAI client directly
    try:
        from openai import OpenAI as DirectOpenAI
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            test_client = DirectOpenAI(api_key=api_key)
            debug_info["direct_client_creation"] = "SUCCESS"

            # Try a simple API call
            try:
                response = test_client.chat.completions.create(
                    model="gpt-5-nano",
                    messages=[{"role": "user", "content": "Say 'Hello!'"}],
                    max_completion_tokens=10
                )
                debug_info["api_call"] = "SUCCESS"
                debug_info["response"] = response.choices[0].message.content
            except Exception as api_error:
                debug_info["api_call"] = "FAILED"
                debug_info["api_error"] = str(api_error)
        else:
            debug_info["direct_client_creation"] = "NO_API_KEY"
    except Exception as e:
        debug_info["direct_client_creation"] = "FAILED"
        debug_info["creation_error"] = str(e)
        import traceback
        debug_info["traceback"] = traceback.format_exc()

    return jsonify(debug_info)

@app.route('/api/debug-chat', methods=['POST'])
def debug_chat():
    """Debug endpoint to test OpenAI directly in chat context"""
    try:
        ensure_initialized()
        data = request.get_json()
        question = data.get('question', 'Test question')

        debug_info = {
            "openai_available": chat_service.openai_client is not None,
            "question": question
        }

        if chat_service.openai_client:
            try:
                # Simple test with gpt-4o-mini
                response = chat_service.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": question}
                    ],
                    max_completion_tokens=100,
                    temperature=0.7
                )
                debug_info["api_call"] = "SUCCESS"
                debug_info["response"] = response.choices[0].message.content
                debug_info["model"] = response.model
            except Exception as e:
                debug_info["api_call"] = "FAILED"
                debug_info["error"] = str(e)
                import traceback
                debug_info["traceback"] = traceback.format_exc()
        else:
            debug_info["api_call"] = "NO_CLIENT"

        return jsonify(debug_info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        # Ensure initialization before processing
        ensure_initialized()

        data = request.get_json()
        # Frontend sends 'question' but also accept 'message' for compatibility
        user_message = data.get('question', data.get('message', ''))

        if not user_message.strip():
            return jsonify({
                "answer": "Please ask me a question about Apple device management or technology!",
                "sources": []
            })

        logger.info(f"Processing question: {user_message}")

        # Use chat service to generate response
        response = chat_service.chat(user_message)

        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error processing chat: {e}")
        return jsonify({
            "error": "An error occurred while processing your request",
            "answer": "I'm experiencing some technical difficulties. Please try again later.",
            "sources": []
        }), 500

@app.route('/api/rebuild-index', methods=['POST'])
def rebuild_index():
    """Rebuild the RAG index from PDFs"""
    try:
        if not RAG_AVAILABLE:
            return jsonify({
                "success": False,
                "message": "RAG system not available in this deployment"
            }), 400

        logger.info("Rebuilding RAG index...")

        # Clear existing cache
        if os.path.exists(rag_system.embeddings_cache_file):
            os.remove(rag_system.embeddings_cache_file)

        # Reinitialize RAG system
        success = rag_system.initialize()
        chat_service.rag_initialized = success

        if success:
            return jsonify({
                "success": True,
                "message": "RAG index rebuilt successfully",
                "document_chunks": len(rag_system.document_chunks)
            })
        else:
            return jsonify({
                "success": False,
                "message": "Failed to rebuild RAG index"
            }), 500
            
    except Exception as e:
        logger.error(f"Failed to rebuild RAG index: {e}")
        return jsonify({
            "success": False,
            "message": f"Error rebuilding RAG index: {str(e)}"
        }), 500

# For local development
if __name__ == '__main__':
    app.run(debug=True)