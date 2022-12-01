import boto3
import json
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

runtime = boto3.client("sagemaker-runtime")

SECRET = os.environ.get("SECRET")
STAGING_SECRET = os.environ.get("STAGING_SECRET")

WIKI2ISO = {
    "as": "asm", # Assamese
    "ast": "ast", # Asturian
    "ay": "ayr", # Central Aymara
    "ba": "bak", # Bashkir
    "bem": "bem", # Bemba
    "ca": "cat", # Catalan
    "ckb": "ckb", # Central Kurdish
    "en": "eng", # English
    "fr": "fra", # French
    "ha": "hau", # Hausa
    "ig": "ibo", # Igbo
    "ilo": "ilo", # Iloko
    "is": "isl", # Icelandic
    "kg": "kon", # Kongo
    "ln": "lin", # Lingala
    "lg": "lug", # Ganda
    "nso": "nso", # Norther Sotho
    "oc": "oci", # Occitan
    "om": "orm", # Oromo
    "pt": "por", # Portuguese
    "ss": "ssw", # Swati
    "qu": "que", # Quechua
    "ru": "rus", # Russian
    "es": "spa", # Spanish
    "ss": "ssw", # Swati
    "ti": "tir", # Tigrinya
    "tn": "tsn", # Tswana
    "ts": "tso", # Tswana
    "wo": "wol", # Wolof
    "zh-yue": "yue", # Yue Chinese
    "yue": "yue",
    "zh": "zho_simp", # Chinese
    "zu": "zul", # Zulu
}

def mk_response(status, headers, body):
    hdrs = { "Content-Type": "application/json" }
    hdrs.update(headers)
    return {
        "statusCode": status,
        "headers": hdrs,
        "body": body,
        "isBase64Encoded": False,
    }


def lambda_handler(event, context):
    # TODO(klausman): handle errors when deserializing request JSON
    data=json.loads(event.get("body"))

    if data.get("secret") not in (SECRET, STAGING_SECRET):
        return mk_response(403, {}, {"error": "No or incorrect API secret specified"})

    endpoint = "nllb200"
    if data.get("secret") == STAGING_SECRET:
        endpoint = "nllb200-staging"

    logging.info("Using endpoint '%s'" , (endpoint))

    for sample in data["samples"]:
        # TODO(klausman): handle broken src/tgt language better
        src = sample.get("sourceLanguage", "sourceLanguageUnset")
        tgt = sample.get("targetLanguage", "targetLanguageUnset")
        try:
            sample["sourceLanguage"] = WIKI2ISO[src]
            sample["targetLanguage"] = WIKI2ISO[tgt]
        except KeyError as e:
            return mk_response(403, {}, {"error": f"Unknown language in {src}->{tgt}. Chose from: {', '.join(WIKI2ISO.keys())}"})

    payload = "\n".join(json.dumps(s) for s in data["samples"])

    # Invoke sagemaker endpoint to get model result
    try:
        response = runtime.invoke_endpoint(
            EndpointName=endpoint,
            ContentType="application/json",
            Body=payload,
        )
        result = response["Body"].read()
    except Exception as ex:
        print("Exception = ", ex)
        return mk_response(500, {}, {"error": "Internal server error: %s"%(ex)})

        raise
    logging.info("Response: %s" % (result))
    return mk_response(200, {"Endpoint": endpoint}, result)
