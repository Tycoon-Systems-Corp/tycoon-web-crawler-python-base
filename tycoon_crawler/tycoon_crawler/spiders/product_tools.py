import os
import json

def detect_product_likely(page):
    try:
        print('Detect Product Likely')
        object_info = {
            "likelihood": 0,
            "type": "unknown"
        }
        # examples: https://www.glossier.com/
        for tag in page.query_selector_all("meta"):
            try:
                property_ = tag.get_attribute("property")
                content = tag.get_attribute("content")
                print(f"Prop", tag, property_, content)
                if property_ == 'og:type' and content == 'product':
                    object_info["likelihood"] = 100
                    object_info["type"] = 'og'
                    return object_info
            except Exception as e:
                print(f"Fail read og:type")
        # examples: https://midnightstudios.live/
        for tag in page.query_selector_all("script"): 
            tag_type = tag.get_attribute("type")
            if tag_type == 'application/ld+json':
                try:
                    content = tag.inner_html()
                    content_data = json.loads(content)
                    print(f"Content Data", content_data)
                    if content_data.get('@type') and content_data['@type'] == 'Product':
                        object_info["likelihood"] = 100
                        object_info["type"] = 'application/ld+json'
                        return object_info
                except Exception as e:
                    print(f"Fail Convert application/ld+json")
                print(f"Script", content)
            # examples https://us.supreme.com/
            elif tag_type == 'application/json':
                try:
                    content = tag.inner_html()
                    content_data = json.loads(content)
                    print(f"Content Data", content_data)
                    if content_data.get('product'):
                        object_info["likelihood"] = 100
                        object_info["type"] = 'application/json'
                        return object_info
                except Exception as e:
                    print(f"Fail Convert application/json")
        return object_info
    except Exception as e:
        print("Exception", str(e))
        return {
            "likelihood": 0,
            "type": "unknown"
        }