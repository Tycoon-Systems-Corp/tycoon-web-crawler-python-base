import os
import json


def detect_product_likely(page):
    try:
        print("Detect Product Likely")
        object_info = {"likelihood": 0, "type": "unknown"}
        # examples: https://www.glossier.com/
        for tag in page.query_selector_all("meta"):
            try:
                property_ = tag.get_attribute("property")
                content = tag.get_attribute("content")
                if property_ == "og:type" and content == "product":
                    object_info["likelihood"] = 100
                    object_info["type"] = "og"
                    return object_info
            except Exception as e:
                print(f"Fail read og:type")
        # examples: https://midnightstudios.live/
        for tag in page.query_selector_all("script"):
            tag_type = tag.get_attribute("type")
            if tag_type == "application/ld+json":
                try:
                    content = tag.inner_html()
                    content_data = json.loads(content)
                    if content_data.get("@type") and content_data["@type"] == "Product":
                        object_info["likelihood"] = 100
                        object_info["type"] = "application/ld+json"
                        return object_info
                except Exception as e:
                    print(f"Fail Convert application/ld+json")
            # examples https://us.supreme.com/
            elif tag_type == "application/json":
                try:
                    content = tag.inner_html()
                    content_data = json.loads(content)
                    if content_data.get("product"):
                        object_info["likelihood"] = 100
                        object_info["type"] = "application/json"
                        return object_info
                except Exception as e:
                    print(f"Fail Convert application/json")
        return object_info
    except Exception as e:
        print("Exception", str(e))
        return {"likelihood": 0, "type": "unknown"}


def get_product_data(page, product_likely):
    object_info = {"product": {}, "price": {}, "images": []}
    try:
        if product_likely.get("type"):
            if product_likely["type"] == "og":
                print("og")
                el_title = object_info["product"]["title"] = page.query_selector(
                    'meta[property="og:title"]'
                )
                if el_title:
                    object_info["product"]["title"] = el_title.get_attribute("content")
                el_desc = page.query_selector('meta[property="og:description"]')
                if el_desc:
                    object_info["product"]["description"] = el_desc.get_attribute(
                        "content"
                    )
                object_info["images"] = get_images(page, "og")
                object_info["price"] = get_price(page, "og")
                print(object_info)
                return object_info
            # TODO: We know that if product likely type is og that we should look for og data but if data is missing we should still look for application/ld+json data
            # We can map through all data if the object_info of current value is None or null
            elif product_likely["type"] == "application/ld+json":
                print("application/ld+json")
                for tag in page.query_selector_all("script"):
                    tag_type = tag.get_attribute("type")
                    if tag_type == "application/ld+json":
                        try:
                            content = tag.inner_html()
                            content_data = json.loads(content)
                            if (
                                content_data.get("@type")
                                and content_data["@type"] == "Product"
                            ):
                                schema_urls_match = [
                                    "http://schema.org/",
                                    "https://schema.org",
                                ]
                                if (
                                    content_data.get("@context")
                                    and content_data["@context"] in schema_urls_match
                                ):
                                    if content_data.get("name"):
                                        object_info["product"]["title"] = content_data[
                                            "name"
                                        ]
                                    if content_data.get("description"):
                                        object_info["product"]["description"] = (
                                            content_data["description"]
                                        )
                                    if content_data.get("image") and isinstance(
                                        content_data["image"], list
                                    ):
                                        object_info["images"] = content_data["image"]
                                    object_info["price"] = get_price(
                                        page, "application/ld+json", content_data
                                    )
                                    if content_data.get("brand"):
                                        brand_data = content_data["brand"]
                                        if brand_data.get("@type") and brand_data.get(
                                            "name"
                                        ):
                                            object_info["product"]["brand"] = (
                                                brand_data["name"]
                                            )
                            return object_info
                        except Exception as e:
                            print("Exception getting Product info application/ld+json")
            elif product_likely["type"] == "application/json":
                print("application/json")
    except Exception as e:
        print("Exception", str(e))
    return object_info


def get_images(page, use_type):
    images = []
    if use_type == "og":
        images_el = page.query_selector_all('meta[property="og:image"]')
        for tag in images_el:
            content = tag.get_attribute("content")
            if content:
                images.append(content)
    return images


def get_price(page, use_type, content_data):
    price = {}
    if use_type == "og":
        el_amount = page.query_selector('meta[property="product:price:amount"]')
        if el_amount:
            price["amount"] = el_amount.get_attribute("content")
        el_currency = page.query_selector('meta[property="product:price:currency"]')
        if el_currency:
            price["currency"] = el_currency.get_attribute("content")
    elif use_type == "application/ld+json" and content_data is not None:
        if content_data.get("offers") and isinstance(content_data["offers"], list):
            offers = content_data["offers"]
            first_offer = None
            for x in offers:
                if x is not None and x.get("price"):
                    first_offer = x
                    break
            if first_offer is not None:
                if first_offer.get("price"):
                    price["amount"] = first_offer["price"]
                if first_offer.get("priceCurrency"):
                    price["currency"] = first_offer["priceCurrency"]
    return price
