"""
Filtres de template pour les dates et durées en français
"""
from django import template
from datetime import timedelta, datetime, date

register = template.Library()


@register.filter
def duration_fr(value):
    """
    Convertit une durée (timedelta ou nombre de jours) en format français
    Ex: "3 jours, 4 heures, 30 minutes"
    """
    if not value:
        return ""
    
    # Si c'est un entier ou float (nombre de jours)
    if isinstance(value, (int, float)):
        days = int(value)
        hours = int((value - days) * 24)
        if hours > 0:
            return f"{days} jour{'s' if days > 1 else ''}, {hours} heure{'s' if hours > 1 else ''}"
        else:
            return f"{days} jour{'s' if days > 1 else ''}"
    
    # Si c'est un timedelta
    if isinstance(value, timedelta):
        days = value.days
        seconds = value.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        
        parts = []
        if days > 0:
            parts.append(f"{days} jour{'s' if days > 1 else ''}")
        if hours > 0:
            parts.append(f"{hours} heure{'s' if hours > 1 else ''}")
        if minutes > 0 and days == 0:  # Afficher les minutes seulement si moins d'un jour
            parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
        
        if not parts:
            return "Moins d'une minute"
        
        return ", ".join(parts)
    
    return str(value)


@register.filter
def date_fr(value):
    """
    Format une date au format français dd/mm/yyyy
    """
    if not value:
        return ""
    
    # Assurer que c'est bien un objet date
    if isinstance(value, datetime):
        value = value.date()
    
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    
    return str(value)