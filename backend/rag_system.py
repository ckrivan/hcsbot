import openai
from typing import List, Dict, Any
import logging
import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGSystem:
    # Common Apple/Jamf acronyms mapping
    ACRONYM_MAP = {
        'ade': 'Automated Device Enrollment',
        'dep': 'Device Enrollment Program',
        'abm': 'Apple Business Manager',
        'asm': 'Apple School Manager',
        'mdm': 'Mobile Device Management',
        'vpp': 'Volume Purchase Program',
        'pppc': 'Privacy Preferences Policy Control',
        'tcc': 'Transparency Consent and Control',
        'apns': 'Apple Push Notification Service',
        'scep': 'Simple Certificate Enrollment Protocol',
        'jamf': 'Jamf Pro',
        'jss': 'Jamf Software Server',
        'laps': 'Local Administrator Password Solution',
        'sso': 'Single Sign-On',
        'saml': 'Security Assertion Markup Language',
        'ldap': 'Lightweight Directory Access Protocol',
        'ad': 'Active Directory',
        'gpo': 'Group Policy Object',
        'byod': 'Bring Your Own Device',
        'maid': 'Managed Apple ID',
        'dscl': 'Directory Service Command Line',
        'kext': 'Kernel Extension',
        'sip': 'System Integrity Protection',
        'filevault': 'FileVault encryption',
        'fv2': 'FileVault 2 encryption',
        'macos': 'macOS operating system',
        'ios': 'iOS operating system',
        'ipados': 'iPadOS operating system',
        'tvos': 'tvOS operating system',
        # Microsoft / Azure terminology (old and new)
        'azure': 'Microsoft Entra ID (formerly Azure Active Directory)',
        'azure ad': 'Microsoft Entra ID (formerly Azure Active Directory)',
        'entra': 'Microsoft Entra ID',
        'entra id': 'Microsoft Entra ID',
        'aad': 'Microsoft Entra ID (formerly Azure Active Directory)',
        # Note: Microsoft 365 mapping handled contextually in expand_acronyms method
        'm365': 'Microsoft 365',
        'office 365': 'Microsoft 365 (formerly Office 365)',
        'o365': 'Microsoft 365 (formerly Office 365)',
    }

    # Map source types to human-readable display names
    SOURCE_TYPE_NAMES = {
        'jamf_nation': 'Jamf Nation community',
        'jamf_docs': 'Jamf documentation',
        'apple_support': 'Apple Support',
        'apple_developer': 'Apple Developer documentation',
        'external_docs': 'external documentation'
    }

    def __init__(self, vector_db):
        self.vector_db = vector_db
        try:
            # Initialize OpenAI client with minimal parameters
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found")
            self.openai_client = openai.OpenAI(api_key=api_key)
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise

    def expand_acronyms(self, query: str) -> str:
        """Expand known acronyms in the query"""
        query_lower = query.lower()
        words = query_lower.split()
        expanded_words = []

        # Product names that should not be expanded (e.g., "Jamf Connect", "Jamf Protect")
        jamf_products = ['connect', 'protect', 'threat', 'school', 'now', 'pro']

        # Special case: Microsoft 365 + Jamf Connect = Entra ID authentication
        # When both appear in query, add Entra ID context
        has_m365 = 'microsoft 365' in query_lower or 'office 365' in query_lower or 'm365' in query_lower or 'o365' in query_lower
        has_jamf_connect = 'jamf connect' in query_lower

        if has_m365 and has_jamf_connect:
            # User is asking about M365 authentication with Jamf Connect = Entra ID setup
            logger.info("Detected Microsoft 365 + Jamf Connect query, adding Entra ID context")
            expanded_words.append("Microsoft Entra ID authentication")

        for i, word in enumerate(words):
            # Remove punctuation for matching
            clean_word = word.strip('.,?!')

            # Special handling for "jamf" - don't expand if followed by a product name
            if clean_word == 'jamf' and i + 1 < len(words):
                next_word = words[i + 1].strip('.,?!')
                if next_word in jamf_products:
                    # Keep "jamf" as-is when part of product name
                    expanded_words.append(word)
                    continue

            if clean_word in self.ACRONYM_MAP:
                expanded_words.append(self.ACRONYM_MAP[clean_word])
                logger.info(f"Expanded acronym: {clean_word} -> {self.ACRONYM_MAP[clean_word]}")
            else:
                expanded_words.append(word)

        return ' '.join(expanded_words)

    def _check_sources_are_old(self, context_docs: List[Dict[str, Any]]) -> bool:
        """Check if all source documents are from before 2024"""
        if not context_docs:
            return False

        # Check if all sources are pre-2024 content based on published_date
        all_old = all(
            self._is_pre_2024(doc.get('published_date', 'pre-2024'))
            for doc in context_docs
        )

        return all_old

    def _is_pre_2024(self, date_str: str) -> bool:
        """Check if a date string represents content from before 2024"""
        if not date_str or date_str == 'pre-2024' or date_str.startswith('pre-'):
            return True

        try:
            # Parse year from ISO date format (YYYY-MM-DD)
            year = int(date_str.split('-')[0])
            return year < 2024
        except:
            return True  # Default to old if can't parse

    def _add_recency_disclaimer(self, answer: str, context_docs: List[Dict[str, Any]], query: str = "") -> str:
        """Add disclaimer if answer is based on old (pre-2024) sources"""
        if self._check_sources_are_old(context_docs):
            # Detect which vendor/service is being asked about
            query_lower = query.lower()

            # Build context-aware vendor links
            vendor_links = []

            # Always include Jamf and Apple
            vendor_links.append("- **Jamf Products:** Visit https://learn.jamf.com for the latest setup guides and release notes")
            vendor_links.append("- **Apple Platforms:** Check https://support.apple.com/guide/deployment/ for current deployment documentation")

            # Add service-specific links based on query context
            if 'okta' in query_lower:
                vendor_links.append("- **Okta:** See https://help.okta.com for current Okta integration documentation")
            elif 'google' in query_lower or 'gsuite' in query_lower or 'workspace' in query_lower:
                vendor_links.append("- **Google Workspace:** Visit https://support.google.com/a for Google Workspace configuration")
            elif 'microsoft' in query_lower or 'entra' in query_lower or 'azure' in query_lower or 'office 365' in query_lower or 'm365' in query_lower or 'o365' in query_lower:
                vendor_links.append("- **Microsoft Services:** See https://learn.microsoft.com/entra for Entra ID and Microsoft 365 configuration")
            elif 'zoom' in query_lower:
                vendor_links.append("- **Zoom:** Visit https://support.zoom.us for the latest Zoom deployment guides")

            # Always add verification reminder
            vendor_links.append("- **Always verify:** Test configurations in a non-production environment first")

            disclaimer = """

---

⚠️ **Important Note:** This information is from 2023 documentation. Some steps and configuration options may have changed since then.

**For the most current and accurate information:**
""" + "\n".join(vendor_links)

            return answer + disclaimer

        return answer

    def generate_response(self, query: str, context_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate response using OpenAI with retrieved context"""
        try:
            # Format context from retrieved documents
            context_text = self._format_context(context_docs)
            
            # Create the prompt
            system_prompt = """You are an expert Apple technology consultant for HCS Technology Group. 
            You help customers with Apple device management, Jamf Pro, iOS/iPadOS deployment, and enterprise Apple solutions.
            
            LANGUAGE STYLE:
            - Use direct, assertive language (e.g., "enforce" not "ensure", "must" not "should", "will" not "might")
            - Write with authority and confidence
            - Use imperative verbs for instructions (Configure, Set, Enable, Implement)
            - Avoid tentative language like "may", "could", "might", "perhaps"
            
            FORMATTING REQUIREMENTS:
            - Use clear numbered lists (1. 2. 3.) for step-by-step instructions
            - Use bullet points (•) for feature lists or options
            - Use bold text for **important terms and concepts**
            - Use `code formatting` for technical terms, commands, and UI elements
            - Structure your response with clear headings (## Main Topics, ### Subtopics)
            - Add visual separators and spacing between sections
            - Use emojis sparingly for visual appeal (⚠️ for warnings, ✅ for success, 📝 for notes)
            - Create clear visual hierarchy with consistent formatting
            - Keep paragraphs short and scannable
            - Use line breaks generously to create white space
            
            Use the provided PDF documentation to answer questions accurately. Always cite your sources with the PDF filename and page number.
            If you can't find the answer in the provided context, state this clearly and directly.
            
            Be concise, professional, authoritative, and focus on practical solutions with excellent visual formatting."""
            
            user_prompt = f"""Question: {query}

Context from HCS Apple documentation:
{context_text}

Please provide a helpful answer based on the documentation above. Include the PDF source and page number for your answer."""

            # Call OpenAI API
            model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')

            # GPT-5 models use max_completion_tokens instead of max_tokens
            api_params = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.1
            }

            # Use appropriate token parameter based on model
            if model.startswith('gpt-5'):
                api_params["max_completion_tokens"] = 600
            else:
                api_params["max_tokens"] = 600

            response = self.openai_client.chat.completions.create(**api_params)
            
            answer = response.choices[0].message.content

            # Add recency disclaimer if sources are from pre-2024 content
            answer = self._add_recency_disclaimer(answer, context_docs, query)

            return {
                'answer': answer,
                'sources': self._extract_sources(context_docs),
                'query': query,
                'context_used': len(context_docs)
            }
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return {
                'answer': "I apologize, but I encountered an error while processing your question. Please try again.",
                'sources': [],
                'query': query,
                'context_used': 0,
                'error': str(e)
            }
    
    def _format_context(self, docs: List[Dict[str, Any]]) -> str:
        """Format retrieved documents into context text"""
        context_parts = []
        
        for i, doc in enumerate(docs, 1):
            context_parts.append(
                f"Source {i}: {doc['filename']} (Page {doc['page_number']})\n"
                f"Content: {doc['text']}\n"
            )
        
        return "\n---\n".join(context_parts)
    
    def _extract_sources(self, docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract source information from retrieved documents"""
        sources = []
        seen_sources = set()

        for doc in docs:
            source_key = f"{doc['filename']}_page_{doc['page_number']}"
            if source_key not in seen_sources:
                sources.append({
                    'filename': doc['filename'],
                    'page_number': doc['page_number'],
                    'similarity_score': doc.get('similarity_score', 0),
                    'published_date': doc.get('published_date', 'pre-2024')
                })
                seen_sources.add(source_key)

        return sources
    
    def ask_question(self, question: str, n_results: int = 5) -> Dict[str, Any]:
        """Complete RAG pipeline: retrieve relevant docs and generate answer"""
        try:
            import time
            start_time = time.time()
            logger.info(f"Processing question: {question}")

            # Expand acronyms in the query
            acronym_start = time.time()
            expanded_question = self.expand_acronyms(question)
            if expanded_question != question:
                logger.info(f"Query after acronym expansion: {expanded_question}")
                question = expanded_question
            logger.info(f"Acronym expansion took {time.time() - acronym_start:.2f}s")

            # Check if this query is about topics not covered in documentation FIRST
            # But only if it's not a known good topic
            if self._is_likely_uncovered_topic(question) and not self._is_known_good_topic(question):
                logger.info(f"Detected uncovered topic: {question}")
                return {
                    'answer': f"I don't have information about **{question}** in our current Apple technology documentation. Our guides primarily cover Jamf Pro device management, iOS deployment, and enterprise Apple integrations.\n\n**Tip:** If you believe this topic should be covered, please use the feedback button to let us know!",
                    'sources': [],
                    'query': question,
                    'context_used': 0,
                    'no_relevant_docs': True
                }
            
            # Retrieve relevant documents
            search_start = time.time()
            relevant_docs = self.vector_db.search_similar(question, n_results=n_results)
            search_time = time.time() - search_start

            # Sort by recency: prioritize recent content (2024+) over old content (pre-2024)
            # Within each group, maintain similarity score order
            def sort_by_recency(doc):
                pub_date = doc.get('published_date', 'pre-2024')

                # Recent content (2024+) gets priority 0, old content gets priority 1
                if pub_date == 'pre-2024':
                    is_recent = 1  # Old content
                else:
                    try:
                        year = int(pub_date.split('-')[0])
                        is_recent = 0 if year >= 2024 else 1
                    except:
                        is_recent = 1  # Default to old if can't parse

                # Negate similarity to sort high scores first within each group
                similarity = -doc.get('similarity_score', 0)
                return (is_recent, similarity)

            relevant_docs = sorted(relevant_docs, key=sort_by_recency)

            # Log similarity scores for debugging
            logger.info(f"Retrieved {len(relevant_docs)} docs in {search_time:.2f}s. Similarity scores: {[doc.get('similarity_score', 0) for doc in relevant_docs]}")
            
            # Use different thresholds for known good topics vs general queries
            if self._is_known_good_topic(question):
                min_similarity_threshold = -0.5  # Very low threshold for topics we know are covered
                logger.info(f"Using very low threshold (-0.5) for known good topic: {question}")
            else:
                min_similarity_threshold = 0.25  # Standard threshold for general queries
            
            filtered_docs = [doc for doc in relevant_docs if doc.get('similarity_score', 0) > min_similarity_threshold]
            
            logger.info(f"After filtering with threshold {min_similarity_threshold}: {len(filtered_docs)} docs remain")
            
            # Additional quality check for multi-word queries
            if len(question.split()) >= 3 and filtered_docs:
                # For multi-word queries, check if the results actually contain most of the key words
                if not self._results_contain_key_words(question, filtered_docs):
                    logger.info(f"Multi-word query '{question}' doesn't have good word matches in results")
                    filtered_docs = []

            # Check if we should search external sources
            # Either no HCS docs, or low confidence results
            best_similarity = max([doc.get('similarity_score', 0) for doc in filtered_docs]) if filtered_docs else 0
            low_confidence = best_similarity < 0.3  # Threshold for low confidence

            if not filtered_docs or low_confidence:
                if low_confidence:
                    logger.info(f"Low confidence HCS results (best: {best_similarity:.3f}), also searching external sources for query: {question}")
                else:
                    logger.info(f"No HCS docs found, falling back to external sources for query: {question}")

                try:
                    external_results = self.jamf_scraper.search_jamf_nation(question, max_results=3)

                    if external_results:
                        logger.info(f"Found {len(external_results)} external results")

                        # Extract full content from top result
                        top_result = external_results[0]
                        full_article = self.jamf_scraper.extract_article(top_result['url'])

                        if full_article and len(full_article.get('content', '')) > 100:
                            # Get source type and display name
                            source_type = full_article.get('source_type', 'external_docs')
                            source_display_name = self.SOURCE_TYPE_NAMES.get(source_type, 'external documentation')

                            # Format as a doc for the RAG system
                            external_docs = [{
                                'text': full_article['content'],
                                'filename': source_display_name.title(),
                                'url': full_article['url'],
                                'page_number': 1,
                                'similarity_score': 0.8,  # High confidence for search results
                                'source_type': source_type,
                                'published_date': full_article.get('published_date', 'recent')
                            }]

                            # Generate response using external content
                            logger.info(f"Generating response using {source_display_name} content")
                            response = self.generate_response(question, external_docs)

                            # Add note about source and link to original page
                            response['answer'] = (
                                f"*Note: This answer is from [{source_display_name}]({full_article['url']}), "
                                "as we didn't find this in our HCS documentation.*\n\n" +
                                response['answer']
                            )

                            # Update sources to show external source
                            response['sources'] = [{
                                'filename': source_display_name.title(),
                                'page_number': 1,
                                'url': full_article['url'],
                                'similarity_score': 0.8,
                                'source_type': source_type
                            }]

                            return response

                    # If external sources also had no results
                    logger.info("No relevant results from external sources either")

                except Exception as e:
                    logger.error(f"Error querying external sources: {e}")

                # Both HCS and external sources had no results
                return {
                    'answer': "I couldn't find relevant information in the HCS Apple documentation or external sources (Jamf Nation, Apple Support, Apple Developer) to answer your question. Please try rephrasing your question or ask about topics covered in our Apple technology guides (Jamf Pro, iOS deployment, device management, etc.).\n\n**Tip:** If you think this should have found results, please use the feedback button to report this issue.",
                    'sources': [],
                    'query': question,
                    'context_used': 0,
                    'no_relevant_docs': True
                }
            
            # Generate response
            generation_start = time.time()
            response = self.generate_response(question, filtered_docs)
            generation_time = time.time() - generation_start

            total_time = time.time() - start_time
            logger.info(f"Generated response using {len(filtered_docs)} source documents in {generation_time:.2f}s (Total: {total_time:.2f}s)")
            return response
            
        except Exception as e:
            logger.error(f"Error in RAG pipeline: {e}")
            return {
                'answer': "I encountered an error while processing your question. Please try again.",
                'sources': [],
                'query': question,
                'context_used': 0,
                'error': str(e)
            }
    
    def _is_likely_uncovered_topic(self, question: str) -> bool:
        """Check if the question is likely about topics not covered in our documentation"""
        question_lower = question.lower()
        
        # Topics we know are NOT covered in the documentation
        uncovered_topics = [
            'jamf security portal', 'jamf security cloud', 'jamf threat defense',
            'jamf private access', 'jamf identity', 'jamf data policy',
            'jamf compliance editor', 'jamf infrastructure manager',
            'microsoft intune', 'workspace one', 'vmware', 'kandji',
            'mosyle', 'addigy', 'fleet', 'simplemdm', 'hexnode',
            'aws', 'google cloud', 'terraform', 'kubernetes',
            'android', 'windows', 'chromebook', 'linux'
        ]
        
        for topic in uncovered_topics:
            if topic in question_lower:
                return True
                
        return False
    
    def _is_known_good_topic(self, question: str) -> bool:
        """Check if the question is about topics we definitely DO cover"""
        question_lower = question.lower()
        
        # Topics we definitely cover in our documentation (based on Apple Style Guide + PDF analysis)
        covered_topics = [
            # Core Apple Technologies & Hardware
            'filevault', 'file vault', 'encryption', 'secure enclave', 'touch id', 'face id',
            'apple business manager', 'abm', 'dep', 'automated enrollment', 'federation',
            'configuration profile', 'ios deployment', 'macos deployment', 'ipados',
            'apple configurator', 'device enrollment', 'mdm', 'mobile device management',
            'bootstrap token', 'apns', 'push certificate', 'maid', 'apple push notification service',
            'mac', 'macbook', 'imac', 'mac mini', 'mac pro', 'mac studio',
            'iphone', 'ipad', 'apple tv', 'apple watch',
            
            # Jamf Products  
            'jamf pro', 'jamf connect', 'jamf school', 'jamf now', 'jamf protect',
            
            # Identity & SSO (confirmed from PDFs)
            'okta', 'google workspace', 'google', 'google sso', 'enterprise connect',
            'azure ad', 'azure', 'microsoft', 'microsoft 365', 'office 365',
            'active directory', 'ldap', 'saml', 'sso', 'single sign-on', 'platform sso',
            'kerberos', 'oauth', 'openid',
            
            # Applications & Services
            'outlook', 'outlook 365', 'microsoft teams', 'chrome', 'enterprise browser',
            'zoom deployment', 'addigy', 'safari', 'app store',
            'icloud', 'icloud for business', 'managed apple id',
            
            # System Management & UI
            'escrow buddy', 'recovery key', 'system settings', 'system information',
            'login window', 'loginwindow', 'screen sharing', 'remote desktop',
            'system preferences', 'control center', 'dock', 'finder', 'launchpad',
            'mission control', 'spaces', 'dashboard', 'notification center',
            'spotlight', 'siri', 'continuity', 'handoff', 'airdrop', 'airplay',
            
            # macOS Versions & Features
            'ios 18', 'ipados 18', 'ipados 16', 'ipados 17',
            'macos sonoma', 'macos sequoia', 'macos ventura', 'macos monterey',
            'silicon macs', 'apple silicon', 'm1', 'm2', 'm3', 'intel',
            'rosetta', 'universal binary',
            
            # Security & Privacy Features
            'gatekeeper', 'xprotect', 'malware removal tool', 'mrt',
            'system integrity protection', 'sip', 'secure boot',
            'privacy preferences policy control', 'pppc', 'tcc',
            'transparency consent and control', 'notarization',
            
            # Networking & Connectivity
            'wifi', 'wi-fi', 'ethernet', 'bluetooth', 'bonjour',
            'vpn', 'ipsec', 'ikev2', 'certificate trust settings',
            'network configuration', 'proxy settings',
            
            # Enterprise Features
            'volume purchase program', 'vpp', 'app assignment',
            'supervised mode', 'activation lock', 'lost mode',
            'remote wipe', 'passcode policy', 'restrictions',
            
            # Security & Certificates
            'smtp', 'app password', 'restore deleted objects',
            'keychain', 'certificate assistant', 'root certificate',
            'identity preference', 'smart card', 'token'
        ]
        
        for topic in covered_topics:
            if topic in question_lower:
                return True
                
        return False
    
    def _results_contain_key_words(self, question: str, results: List[Dict[str, Any]]) -> bool:
        """Check if the search results actually contain key words from the multi-word query"""
        # Extract key words from question (remove common words)
        stop_words = {'how', 'do', 'i', 'to', 'the', 'a', 'an', 'is', 'are', 'what', 'where', 'when', 'why', 'with', 'for', 'on', 'in', 'at', 'and', 'or', 'but'}
        question_words = [word.lower().strip('?.,!') for word in question.split() if len(word) > 2 and word.lower() not in stop_words]
        
        if len(question_words) < 2:
            return True  # Single key word queries are fine
            
        # Combine all result text
        all_result_text = ' '.join([result.get('text', '').lower() for result in results])
        
        # Check if at least 50% of key words appear in results
        matching_words = sum(1 for word in question_words if word in all_result_text)
        match_ratio = matching_words / len(question_words)
        
        logger.info(f"Key words: {question_words}, Match ratio: {match_ratio}")
        return match_ratio >= 0.5  # At least 50% of key words should match
    
    def get_sample_questions(self) -> List[str]:
        """Return sample questions for demo purposes"""
        return [
            "How do I deploy Zoom using Jamf Pro?",
            "What are the requirements for iOS 18 device management?",
            "How do I set up Apple Configurator 2 blueprints?",
            "What is the process for enrolling devices in Apple Business Manager?",
            "How do I configure Microsoft 365 with Jamf Connect?",
            "What are the steps for setting up Bootstrap Token?",
            "How do I manage Apple TV devices through ABM?",
            "What is the process for macOS Sonoma deployment?"
        ]