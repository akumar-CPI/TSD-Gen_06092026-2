# schema_map.py
#
# Maps a pallet function's *resolved* type (see resolve_pallet_type() in
# parse_iflow.py) to the exact table layout used in the TSD template.
# Covers every pallet function section present in the template.
#
# Each schema is:
#   {
#     "verified": True/False,
#     "title": "<Heading text used in the generated doc>",
#     "sections": [
#         ("<Sub-table header>", [("<Label>", <field-spec>), ...]),
#     ],
#   }
#
# verified=True  -> property names checked against a real production
#                    iFlow export. Trust these.
# verified=False -> the table LABELS match the template exactly, but the
#                    underlying property key names are a best-effort
#                    guess (from SAP CPI documentation / typical naming
#                    conventions), not yet confirmed against a real
#                    export. If a field shows up blank for a step you
#                    know has that setting configured, check
#                    parsed.json's raw "properties" for that element and
#                    correct the key name here - the label/structure is
#                    already right either way, so this is a quick fix,
#                    not a redesign.
#
# <field-spec> is one of:
#   "PropKey"                                    -> plain value
#   "__NAME__"                                    -> the element's name
#   {"bool": "PropKey"}                           -> single check, no label
#   {"prop": "PropKey", "checkbox": [...]}        -> raw value == label
#   {"prop": "PropKey", "checkbox": {"raw": "Label"}} -> raw value -> label map
#   ["PropKeyA", "PropKeyB"]                      -> first non-empty wins
#
# ONLY fields listed here are ever rendered - there is no "dump every
# property" fallback. If it's not in the template, it doesn't belong here.

PALLET_SCHEMAS = {
    # =====================================================================
    # VERIFIED against a real production iFlow export
    # =====================================================================
    "ContentModifier": {
        "verified": True,
        "title": "Content Modifier",
        "sections": [
            ("General", [("Name", "__NAME__")]),
            ("Message Body", [
                ("Type", {"prop": "bodyType", "checkbox": {"constant": "Constant", "expression": "Expression"}}),
                ("Body", "bodyContent"),
            ]),
            # Message Header / Exchange Property come from headerTable /
            # propertyTable - nested CPI "table inside a property" values,
            # auto-detected and rendered separately by generate_tsd.py.
        ],
    },
    "GroovyScript": {
        "verified": True,
        "title": "Groovy Script",
        "sections": [
            ("General", [("Name", "__NAME__")]),
            ("Processing", [("Script File", "script"), ("Script Function", "scriptFunction")]),
        ],
    },
    "ExternalCall": {
        "verified": True,
        "title": "Request-Reply (External Call)",
        "sections": [("General", [("Name", "__NAME__")])],
    },
    "ExclusiveGateway": {
        "verified": True,
        "title": "Router",
        "sections": [
            ("General", [
                ("Name", "__NAME__"),
                ("Error Handling", {"bool": "throwException"}),
            ]),
            # Route Conditions table (Order/Route Name/Conditional
            # Expression/Default Route) is rendered separately by
            # generate_tsd.py from sequenceFlow data, not a property.
        ],
    },
    "ProcessCallElement": {
        "verified": True,
        "title": "Process Call",
        "sections": [
            ("General", [("Name", "__NAME__")]),
            ("Processing", [("Local Integration Process", "processId")]),
        ],
    },
    "DBstorage_Get": {
        "verified": True,
        "title": "Get (Data Store Operations)",
        "sections": [
            ("General", [("Name", "__NAME__")]),
            ("Processing", [
                ("Data Store Name", "storageName"),
                ("Visibility", {"prop": "visibility", "checkbox": {"global": "Global", "local": "Integration Flow"}}),
                ("Entry ID", "dataStoreId"),
                ("Delete On Completion", {"bool": "delete"}),
                ("Throw Exception on Missing Entry", {"bool": "stopOnMissingEntry"}),
            ]),
        ],
    },
    "JsonToXmlConverter": {
        "verified": True,
        "title": "JSON to XML Convertor",
        "sections": [
            ("General", [
                ("Name", "__NAME__"),
                ("Use Namespace Mapping", {"bool": "useNamespaces"}),
            ]),
            ("Processing", [
                ("JSON Prefix Separator", "jsonNamespaceSeparator"),
                ("Add XML Root Element", {"bool": "addXMLRootElement"}),
            ]),
        ],
    },
    "GeneralSplitter": {
        "verified": True,
        "title": "General Splitter",
        "sections": [
            ("General", [
                ("Name", "__NAME__"),
                ("Expression Type", {"prop": "exprType", "checkbox": {"xpath": "XPATH", "linebreak": "Line Break"}}),
                ("Xpath Expression", "splitExprValue"),
                ("Grouping", "grouping"),
                ("Time Out (in S)", "timeOut"),
                ("Streaming", {"bool": "Streaming"}),
                ("Parallel Processing", {"bool": "ParallelProcessing"}),
                ("Stop on Exception", {"bool": "StopOnExecution"}),
            ]),
        ],
    },
    "IteratingSplitter": {
        "verified": True,
        "title": "Iterating Splitter",
        "sections": [
            ("General", [
                ("Name", "__NAME__"),
                ("Expression Type", {"prop": "exprType", "checkbox": {"xpath": "XPATH", "linebreak": "Line Break", "token": "Token"}}),
                ("Xpath Expression", "splitExprValue"),
                ("Token", "tokenValue"),
                ("Grouping", "grouping"),
                ("Time Out (in S)", "timeOut"),
                ("Streaming", {"bool": "Streaming"}),
                ("Parallel Processing", {"bool": "ParallelProcessing"}),
                ("Stop on Exception", {"bool": "StopOnExecution"}),
            ]),
        ],
    },
    "XSLTMapping": {
        "verified": True,
        "title": "XSLT Mapping",
        "sections": [
            ("General", [("Name", "__NAME__")]),
            ("Processing", [
                ("Source", "mappingSource"),
                ("Resource", "mappinguri"),
                ("Output Format", "mappingoutputformat"),
            ]),
        ],
    },

    # =====================================================================
    # BEST-EFFORT (labels match the template exactly; property key names
    # not yet confirmed against a real export for these specific types)
    # =====================================================================
    "ContentEnricher": {
        "verified": False,
        "title": "Content Enricher",
        "sections": [
            ("General", [("Name", "__NAME__")]),
            ("Processing", [
                ("Aggregation Algorithm", {"prop": "aggregationAlgorithm", "checkbox": ["Combine", "Enrich"]}),
                ("Original Message", "sourceMessageBody"),
                ("Path to Node", "xpathSourceMessage"),
                ("Key Element", "xpathSourceMessageForKey"),
                ("Lookup Message", "lookupMessageBody"),
                ("Path to Node", "xpathLookupMessage"),
                ("Key Element", "xpathLookupMessageForKey"),
            ]),
        ],
    },
    "Send": {
        "verified": False,
        "title": "Send",
        "sections": [("General", [("Name", "__NAME__")])],
    },
    "LoopingProcessCallElement": {
        "verified": False,
        "title": "Looping Process Call",
        "sections": [
            ("General", [("Name", "__NAME__")]),
            ("Processing", [
                ("Local Integration Process", "processId"),
                ("Expression Type", {"prop": "expressionType", "checkbox": ["XML", "Non-XML"]}),
                ("Condition Expression", "conditionExpression"),
                ("Max. Number of Iterations", "maxIterations"),
            ]),
        ],
    },
    "MessageMapping": {
        "verified": False,
        "title": "Message Mapping",
        "sections": [
            ("General", [("Name", "__NAME__")]),
            ("Processing", [("Resource", "mappinguri")]),
        ],
    },
    "OperationMapping": {
        "verified": False,
        "title": "Operation Mapping",
        "sections": [
            ("General", [("Name", "__NAME__")]),
            ("Processing", [("Resource", "mappinguri")]),
        ],
    },
    "XmlToJsonConverter": {
        "verified": False,
        "title": "XML to JSON Convertor",
        "sections": [
            ("General", [
                ("Name", "__NAME__"),
                ("Use Namespace Mapping", {"bool": "useNamespaceMapping"}),
            ]),
            ("Processing", [
                ("JSON Prefix Separator", "jsonNamespaceSeparator"),
                ("JSON Output Encoding", "jsonOutputEncoding"),
                ("Suppress Root Element", {"bool": "suppressJsonRootElement"}),
                ("Streaming", {"bool": "streaming"}),
            ]),
        ],
    },
    "CsvToXmlConverter": {
        "verified": False,
        "title": "CSV to XML Convertor",
        "sections": [
            ("General", [("Name", "__NAME__")]),
            ("Processing", [
                ("XML Schema", "schemaLocation"),
                ("Path to target XML in XSD", "targetXpath"),
                ("Record Marker in CSV", "recordSetStructure"),
                ("Field Separator in CSV", "fieldSeparator"),
                ("Exclude First Line Header", {"bool": "includeHeaderLine"}),
            ]),
        ],
    },
    "XmlToCsvConverter": {
        "verified": False,
        "title": "XML to CSV Convertor",
        "sections": [
            ("General", [("Name", "__NAME__")]),
            ("Processing", [
                ("XML Schema", "schemaLocation"),
                ("Path to Source Element XML in XSD", "sourceXpath"),
                ("Field Separator in CSV", "fieldSeparator"),
                ("Include First Line Header", {"bool": "includeHeaderLine"}),
                ("Include Parent Element", "includeParentElement"),
                ("Path to Parent Element", "parentElementXpath"),
                ("Include Attribute Values", {"bool": "includeAttributeValues"}),
            ]),
        ],
    },
    "GzipCompress": {"verified": False, "title": "GZIP Compression", "sections": [("General", [("Name", "__NAME__")])]},
    "GzipDecompress": {"verified": False, "title": "GZIP Decompression", "sections": [("General", [("Name", "__NAME__")])]},
    "Base64Encoder": {"verified": False, "title": "Base64 Encoder", "sections": [("General", [("Name", "__NAME__")])]},
    "Base64Decoder": {"verified": False, "title": "Base64 Decode", "sections": [("General", [("Name", "__NAME__")])]},
    "ZipCompress": {"verified": False, "title": "ZIP Compression", "sections": [("General", [("Name", "__NAME__")])]},
    "ZipDecompress": {"verified": False, "title": "ZIP Decompression", "sections": [("General", [("Name", "__NAME__")])]},
    "MimeMultipartDecoder": {
        "verified": False,
        "title": "MIME Multipart Decoder",
        "sections": [
            ("General", [("Name", "__NAME__")]),
            ("Processing", [("Multipart Header Line", {"bool": "multipartHeaderLine"})]),
        ],
    },
    "MimeMultipartEncoder": {
        "verified": False,
        "title": "MIME Multipart Encoder",
        "sections": [
            ("General", [("Name", "__NAME__")]),
            ("Processing", [
                ("Multipart Subtype", {"prop": "multipartSubtype", "checkbox": ["Alternative", "Digest", "Mixed", "Parallel", "Related"]}),
                ("Add Multipart Header Line", {"bool": "addMultipartHeaderLine"}),
                ("Include Headers", "includeHeaders"),
            ]),
        ],
    },
    "Filter": {
        "verified": False,
        "title": "Filter",
        "sections": [
            ("General", [("Name", "__NAME__")]),
            ("Processing", [
                ("Xpath Expression", "xpathExpressionFilter"),
                ("Value Type", {"prop": "valueType", "checkbox": ["Boolean", "Integer", "Node", "Nodelist", "String"]}),
            ]),
        ],
    },
    "MessageDigest": {
        "verified": False,
        "title": "Message Digest",
        "sections": [
            ("General", [("Name", "__NAME__")]),
            ("Processing", [
                ("Filter (Xpath)", "digestXpath"),
                ("Canonicalization Method", {"prop": "canonicalizationMethod", "checkbox": [
                    "Canonical XML Version 1.0", "Canonical XML with Comments version 1.0",
                    "Exclusive XML Canonicalization Version 1.0",
                    "Exclusive XML Canonicalization with comments Version 1.0", "None"]}),
                ("Digest Algorithm", {"prop": "digestAlgorithm", "checkbox": ["MD5", "SHA1", "SHA256", "SHA384", "SHA512"]}),
                ("Target Header", "targetHeader"),
            ]),
        ],
    },
    "JavaScript": {
        "verified": False,
        "title": "Java Script",
        "sections": [
            ("General", [("Name", "__NAME__")]),
            ("Processing", [("Script File", "script"), ("Script Function", "scriptFunction")]),
        ],
    },
    "Aggregator": {
        "verified": False,
        "title": "Aggregator",
        "sections": [
            ("General", [("Name", "__NAME__")]),
            ("Correlation", [("Correlation Expression (Xpath)", "correlExpression")]),
            ("Aggregation Strategy", [
                ("Incoming Format", "incomingFormat"),
                ("Aggregation Algorithm", {"prop": "aggregationAlgorithm", "checkbox": ["Combine", "in Sequence"]}),
                ("Last Message Condition (Xpath)", "lastMessageCondition"),
                ("Message Sequence Expression (Xpath)", "predSuccExpression"),
                ("Completion Timeout (in min)", "completionTimeout"),
                ("Data Store Name", "datastore"),
            ]),
        ],
    },
    "Gather": {
        "verified": False,
        "title": "Gather",
        "sections": [
            ("General", [("Name", "__NAME__")]),
            ("Aggregation Strategy", [
                ("Incoming Format", {"prop": "incomingFormat", "checkbox": ["Plain Text", "XML (Different Format)", "XML (Same Format)"]}),
                ("Aggregation Algorithm", {"prop": "aggregationAlgorithm", "checkbox": ["Combine at Xpath", "Concatenate"]}),
                ("Combine from Source (Xpath)", "sourceXpath"),
                ("Combine at Target (Xpath)", "targetXpath"),
            ]),
        ],
    },
    "Join": {"verified": False, "title": "Join", "sections": [("General", [("Name", "__NAME__")])]},
    "Multicast": {
        "verified": False,
        "title": "Sequential Multicast",
        "sections": [("General", [("Name", "__NAME__")])],
    },
    "ParallelMulticast": {
        "verified": False,
        "title": "Parallel Multicast",
        "sections": [("General", [("Name", "__NAME__")])],
    },
    "PkcsSplitter": {
        "verified": False,
        "title": "PCKS#7/CMS Splitter",
        "sections": [
            ("General", [
                ("Payload File Name", "payloadFileName"),
                ("Signature File Name", "signatureFileName"),
                ("Wrap by Content info", {"bool": "wrapByContentInfo"}),
                ("Payload First", {"bool": "payloadFirst"}),
                ("Base64 Payload", {"bool": "base64Payload"}),
                ("Base64 Signature", {"bool": "base64Signature"}),
            ]),
        ],
    },
    "XmlValidator": {
        "verified": False,
        "title": "XML Validator",
        "sections": [
            ("General", [("Name", "__NAME__")]),
            ("Validation", [
                ("XML Schema", "schemaLocation"),
                ("Prevent Exception on Failure", {"bool": "continueOnException"}),
            ]),
        ],
    },
    "WriteVariables": {
        "verified": False,
        "title": "Write Variables",
        "sections": [
            ("General", [("Name", "__NAME__")]),
            ("Processing", [
                ("Name", "variableName"),
                ("Type", {"prop": "variableType", "checkbox": ["Constant", "Expression", "External Parameter", "Header", "Property", "XPath"]}),
                ("Data Type", "dataType"),
                ("Value", "variableValue"),
                ("Global Scope", {"bool": "globalScope"}),
            ]),
        ],
    },
    "Persist": {
        "verified": False,
        "title": "Persist",
        "sections": [
            ("General", [("Name", "__NAME__")]),
            ("Processing", [("Step ID", "stepId"), ("Encrypt Stored Message", {"bool": "encryption"})]),
        ],
    },
    "DBstorage_Select": {
        "verified": False,
        "title": "Select (Data Store Operations)",
        "sections": [
            ("General", [("Name", "__NAME__")]),
            ("Processing", [
                ("Data Store Name", "storageName"),
                ("Visibility", {"prop": "visibility", "checkbox": {"global": "Global", "local": "Integration Flow"}}),
                ("Number of Polled Messages", "polledEntries"),
                ("Delete On Completion", {"bool": "delete"}),
            ]),
        ],
    },
    "DBstorage_Write": {
        "verified": False,
        "title": "Write (Data Store Operations)",
        "sections": [
            ("General", [("Name", "__NAME__")]),
            ("Processing", [
                ("Data Store Name", "storageName"),
                ("Visibility", {"prop": "visibility", "checkbox": {"global": "Global", "local": "Integration Flow"}}),
                ("Entry ID", "dataStoreId"),
                ("Retention Threshold for Alerting (in d)", "graceperiod"),
                ("Expiration Period (in d)", "overallDuration"),
                ("Encrypt Stored Message", {"bool": "encryption"}),
                ("Overwrite Existing Message", {"bool": "overwrite"}),
            ]),
        ],
    },
    "DBstorage_Delete": {
        "verified": False,
        "title": "Delete (Data Store Operations)",
        "sections": [
            ("General", [("Name", "__NAME__")]),
            ("Processing", [
                ("Data Store Name", "storageName"),
                ("Visibility", {"prop": "visibility", "checkbox": {"global": "Global", "local": "Integration Flow"}}),
                ("Entry ID", "dataStoreId"),
            ]),
        ],
    },
    "DBstorage_Persist": {
        "verified": False,
        "title": "Persist (Data Store Operations)",
        "sections": [
            ("General", [("Name", "__NAME__")]),
            ("Processing", [("Encrypt Stored Message", {"bool": "encryption"})]),
        ],
    },

    # ---- Security: Decryptor / Encryptor / Signer / Verifier ----
    # These carry many template fields (full XAdES sub-detail is out of
    # scope - see README); core fields per the template are included.
    "PKCS7Decryptor": {
        "verified": False,
        "title": "PKCS7 Decryptor / CMS Decryptor",
        "sections": [
            ("General", [
                ("Name", "__NAME__"),
                ("Body is Base64 Encoded", {"bool": "base64Encoded"}),
                ("Signatures", {"prop": "signatures", "checkbox": [
                    "Enveloped Data Only", "Enveloped or \u201cSigned and Enveloped\u201d Data", "Signed and Enveloped Data"]}),
                ("Public Key Alias", "alias"),
            ]),
        ],
    },
    "PGPDecryptor": {
        "verified": False,
        "title": "PGP Decryptor",
        "sections": [
            ("General", [
                ("Name", "__NAME__"),
                ("Signatures", {"prop": "signatures", "checkbox": ["None Expected", "Optional", "Required"]}),
                ("Signer Key User IDs", "signerUserId"),
            ]),
        ],
    },
    "PKCS7Encryptor": {
        "verified": False,
        "title": "PKCS7 / CMS Encryptor",
        "sections": [
            ("General", [
                ("Name", "__NAME__"),
                ("Block size (in Bytes)", "blockSize"),
                ("Encode body with Base64", {"bool": "base64Encoded"}),
                ("Signatures", {"prop": "signatures", "checkbox": ["Enveloped Data Only", "Signed and Enveloped Data"]}),
                ("Content Encryption Algorithm", "encryptionAlgorithm"),
                ("Secret Key Length", "secretKeyLength"),
                ("Receiver Public Key Alias", "alias"),
            ]),
        ],
    },
    "PGPEncryptor": {
        "verified": False,
        "title": "PGP Encryptor",
        "sections": [
            ("General", [
                ("Name", "__NAME__"),
                ("Signatures", {"prop": "signatures", "checkbox": ["Including", "None"]}),
                ("Content Encryption Algorithm", "encryptionAlgorithm"),
                ("Secret Key Length", "secretKeyLength"),
                ("Compression Algorithm", "compressionAlgorithm"),
                ("Encryption Key User IDs", "recipientUserId"),
            ]),
        ],
    },
    "PKCS7Signer": {
        "verified": False,
        "title": "PKCS7Signer",
        "sections": [
            ("General", [
                ("Name", "__NAME__"),
                ("Block Size (in bytes)", "blockSize"),
                ("Include Content in Signed Data", {"bool": "includeContent"}),
                ("Encode Signed data with Base64", {"bool": "base64Encoded"}),
                ("Private Key Alias", "alias"),
                ("Signature Algorithm", "signatureAlgorithm"),
                ("Include Certificates", {"bool": "includeCertificates"}),
                ("Include Signing Time", {"bool": "includeSigningTime"}),
            ]),
        ],
    },
    "SimpleSigner": {
        "verified": False,
        "title": "Simple Signer",
        "sections": [
            ("General", [
                ("Name", "__NAME__"),
                ("Private Key Alias", "alias"),
                ("Signature Algorithm", "signatureAlgorithm"),
                ("Signature Header Name", "headerName"),
            ]),
        ],
    },
    "XMLSigner": {
        "verified": False,
        "title": "XMLSigner",
        "sections": [
            ("General", [
                ("Name", "__NAME__"),
                ("Private Key Alias", "alias"),
                ("Signature Algorithm", "signatureAlgorithm"),
                ("Digest Algorithm", "digestAlgorithm"),
                ("Signature Type", "signatureType"),
                ("XML Schema File Path", "schemaLocation"),
            ]),
        ],
    },
    "PKCS7Verifier": {
        "verified": False,
        "title": "PKCS7 Signature Verifier",
        "sections": [
            ("General", [
                ("Name", "__NAME__"),
                ("Header is Base64 Encoded", {"bool": "headerBase64Encoded"}),
                ("Body is Base64 Encoded", {"bool": "base64Encoded"}),
                ("Public Key Aliases", "alias"),
            ]),
        ],
    },
    "XMLVerifier": {
        "verified": False,
        "title": "XML Signature Verifier",
        "sections": [
            ("General", [
                ("Name", "__NAME__"),
                ("Expected Signature Type", "signatureType"),
                ("XML Schema File Path", "schemaLocation"),
                ("Check for Key Info Element", {"bool": "checkKeyInfo"}),
                ("Public Key Aliases", "alias"),
            ]),
        ],
    },

    # ---- Timer / Escalation End ----
    "TimerStartEvent": {
        "verified": False,
        "title": "Timer",
        "sections": [
            ("General", [("Name", "__NAME__")]),
            ("Scheduler", [
                ("Occurrence", {"prop": "occurrence", "checkbox": ["Run Once", "Schedule on Day", "Schedule to recur"]}),
                ("On Date", "startDate"),
                ("On Time", "startTime"),
                ("Time Zone", "timeZone"),
                ("Every (Sec)", "everySec"),
            ]),
        ],
    },
    "EscalationEndEvent": {
        "verified": False,
        "title": "Escalation End",
        "sections": [
            ("General", [
                ("Category", {"prop": "category", "checkbox": [
                    "Receiver not found", "Routing conditions not met", "Receiver not reachable",
                    "Not Authenticated to invoke receiver", "Not Authorized to invoke receiver",
                    "Receiver tries to redirect", "Internal server error in receiver", "Others - not further qualified"]}),
            ]),
        ],
    },
}

ADAPTER_SCHEMAS = {
    # =====================================================================
    # VERIFIED
    # =====================================================================
    "http|receiver": {
        "verified": True,
        "title": "HTTP (HTTP - Receiver)",
        "sections": [
            ("General", [
                ("Name", "__NAME__"),
                ("Adapter / Component Type", "ComponentType"),
                ("Transport Protocol", "TransportProtocol"),
                ("Message Protocol", "MessageProtocol"),
            ]),
            ("Connection", [
                ("Address / Endpoint URL", ["Address", "httpAddressWithoutQuery"]),
                ("HTTP Method", "httpMethod"),
                ("Authentication Method", "authenticationMethod"),
                ("Credential Name", "credentialName"),
                ("Private Key Alias", "privateKeyAlias"),
                ("Location ID", "locationID"),
                ("Proxy Type", "proxyType"),
                ("Proxy Host", "proxyHost"),
                ("Proxy Port", "proxyPort"),
                ("Timeout (in ms)", "httpRequestTimeout"),
            ]),
            ("Processing", [
                ("Allowed Request Headers", "allowedRequestHeaders"),
                ("Allowed Response Headers", "allowedResponseHeaders"),
                ("Should Send Body", {"bool": "httpShouldSendBody"}),
                ("Throw Exception on Failure", {"bool": "throwExceptionOnFailure"}),
                ("Retry on Connection Failure", {"bool": "retryOnConnectionFailure"}),
                ("Retry Iteration", "retryIteration"),
                ("Retry Interval", "retryInterval"),
            ]),
        ],
    },
    "mail|receiver": {
        "verified": True,
        "title": "MAIL Receiver",
        "sections": [
            ("General", [("Name", "__NAME__")]),
            ("Connection", [
                ("Server", "server"), ("From", "from"), ("To", "to"),
                ("CC", "cc"), ("Subject", "subject"), ("Content Type", "content_type"),
            ]),
        ],
    },

    # =====================================================================
    # BEST-EFFORT (labels match template; property names not yet
    # independently confirmed for these specific adapter/direction pairs)
    # =====================================================================
    "http|sender": {
        "verified": False,
        "title": "HTTP Sender",
        "sections": [
            ("General", [("Name", "__NAME__")]),
            ("Connection", [
                ("Address", "Address"),
                ("Authorization", "authenticationMethod"),
                ("User Role", "userRole"),
                ("CSRF Protected", {"bool": "csrfProtected"}),
            ]),
        ],
    },
    "https|sender": {
        "verified": False,
        "title": "HTTPS Sender",
        "sections": [
            ("General", [("Name", "__NAME__")]),
            ("Connection", [("Address", "Address"), ("User Role", "userRole")]),
        ],
    },
    "https|receiver": {
        "verified": False,
        "title": "HTTP Receiver",
        "sections": [
            ("General", [("Name", "__NAME__")]),
            ("Connection", [("Address", ["Address", "httpAddressWithoutQuery"]), ("Proxy Type", "proxyType")]),
        ],
    },
    "sftp|sender": {
        "verified": False,
        "title": "SFTP Sender",
        "sections": [
            ("General", [("Name", "__NAME__")]),
            ("Source", [("Directory", "directory"), ("FileName", "fileName"), ("Address", "Address")]),
        ],
    },
    "sftp|receiver": {
        "verified": False,
        "title": "SFTP Receiver",
        "sections": [
            ("General", [("Name", "__NAME__")]),
            ("Target", [("Directory", "directory"), ("File Name", "fileName"), ("Address", "Address")]),
        ],
    },
    "processdirect|sender": {
        "verified": False,
        "title": "Process Direct Sender",
        "sections": [("General", [("Name", "__NAME__")]), ("Connection", [("Address", "Address")])],
    },
    "processdirect|receiver": {
        "verified": False,
        "title": "Process Direct Receiver",
        "sections": [("General", [("Name", "__NAME__")]), ("Connection", [("Address", "Address")])],
    },
    "soap|sender": {
        "verified": False,
        "title": "SOAP Sender",
        "sections": [("General", [("Name", "__NAME__")]), ("Connection", [("Address", "Address")])],
    },
    "soap|receiver": {
        "verified": False,
        "title": "SOAP Receiver",
        "sections": [("General", [("Name", "__NAME__")]), ("Connection", [("Address", "Address")])],
    },
    "idoc|sender": {
        "verified": False,
        "title": "IDOC Sender",
        "sections": [("General", [("Name", "__NAME__")]), ("Connection", [("Address", "Address")])],
    },
    "idoc|receiver": {
        "verified": False,
        "title": "IDOC Receiver",
        "sections": [("General", [("Name", "__NAME__")]), ("Connection", [("Address", "Address")])],
    },
    "odata|sender": {
        "verified": False,
        "title": "ODATA Sender",
        "sections": [("General", [("Name", "__NAME__")]), ("Adapter-Specific", [("Operation", "operation")])],
    },
    "odata|receiver": {
        "verified": False,
        "title": "ODATA Receiver",
        "sections": [
            ("General", [("Name", "__NAME__")]),
            ("Adapter-Specific", [("Address", "Address"), ("Operation", "operation")]),
        ],
    },
    "xi|sender": {
        "verified": False,
        "title": "XI Sender",
        "sections": [("General", [("Name", "__NAME__")]), ("Connection", [("Address", "Address")])],
    },
    "xi|receiver": {
        "verified": False,
        "title": "XI Receiver",
        "sections": [("General", [("Name", "__NAME__")]), ("Connection", [("Address", "Address")])],
    },
    "rfc|receiver": {
        "verified": False,
        "title": "RFC Receiver",
        "sections": [("General", [("Name", "__NAME__")]), ("Adapter-Specific", [("Destination", "rfcDestination")])],
    },
}
