from django import template

register = template.Library()

MODEL_VERBOSE_NAMES = {
    'student': 'Student',
    'classfee': 'Class Fee',
    'feepayment': 'Fee Payment',
    'feerecord': 'Fee Record',
    'customuser': 'User',
    'group': 'Group',
}

@register.filter
def get_attr(obj, attr_name):
    """Retrieve an attribute or item from an object/dictionary."""
    if hasattr(obj, attr_name):
        res = getattr(obj, attr_name)
        if callable(res):
            return res()
        return res
    if isinstance(obj, dict):
        return obj.get(attr_name)
    return None

@register.filter
def replace_underscore(value):
    """Replace underscores with spaces."""
    if not isinstance(value, str):
        return value
    return value.replace('_', ' ')

@register.filter
def verbose_name(value):
    """Convert a raw model key to a human-readable label."""
    if not isinstance(value, str):
        return value
    return MODEL_VERBOSE_NAMES.get(value.lower(), value.replace('_', ' ').title())

@register.filter
def has_permission(user, perm):
    """Check if user has a specific permission."""
    if not user or not hasattr(user, 'has_perm'):
        return False
    return user.has_perm(perm)
