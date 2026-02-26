from django.conf import settings
from django.urls import reverse, NoReverseMatch

def sidebar_context(request):
    sidebar = []
    current_path = request.path

    for group in settings.SIDEBAR_CONFIG:
        group_data = {
            "title": group["title"],
            "items": []
        }
        for item in group["items"]:
            url = "#"
            is_active = False
            args = item.get("args", [])
            
            if "url" in item:
                try:
                    url = reverse(item["url"], args=args)
                    # For generic list, check if current path matches EXACTLY or starts with
                    # but if it's a list view, we want to match more strictly to avoid highlights overlap
                    if url != "/" and current_path.startswith(url):
                        is_active = True
                    elif url == "/" and current_path == "/":
                        is_active = True
                except Exception:
                    url = "#"
            
            item_data = {
                "label": item["label"],
                "url": url,
                "icon": item.get("icon", "🔹"),
                "is_active": is_active,
                "action": item.get("action", None)
            }
            group_data["items"].append(item_data)
        sidebar.append(group_data)

    return {"SIDEBAR_CONFIG": sidebar}
