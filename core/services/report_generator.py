"""
Child activity report generation service
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from django.db.models import Q, Count
from core.models import Child, ActivityResult, User


class ChildReportGenerator:
    """Generate activity reports for children"""
    
    def __init__(self, days_lookback: int = 30):
        """
        Initialize report generator
        Args:
            days_lookback: Number of days to include in report (default: 30)
        """
        self.days_lookback = days_lookback
        self.date_from = datetime.now() - timedelta(days=days_lookback)
    
    def generate_child_report(self, child: Child) -> Dict[str, any]:
        """
        Generate activity report for a single child
        Args:
            child: Child instance
        Returns:
            dict: Report data with statistics and recent activities
        """
        activities = ActivityResult.objects.filter(
            student=child,
            created_at__gte=self.date_from
        ).order_by('-created_at')
        
        total_activities = activities.count()
        achieved_activities = activities.filter(
            activity_result__isnull=False
        ).exclude(
            activity_result=''
        ).exclude(
            activity_result='Tentadu'
        ).count()
        
        achievement_rate = (achieved_activities / total_activities * 100) if total_activities > 0 else 0
        
        # Group by theme
        themes = activities.values('category1').annotate(count=Count('id')).order_by('-count')
        
        # Get recent activities for detailed view
        recent = activities[:10]
        
        return {
            'child_name': child.first_name,
            'child_id': str(child.id),
            'age_group': child.get_age_group_display(),
            'parent_name': child.parent.get_full_name(),
            'total_activities': total_activities,
            'achieved_activities': achieved_activities,
            'achievement_rate': round(achievement_rate, 1),
            'themes': list(themes),
            'recent_activities': [
                {
                    'name': act.activity_name,
                    'result': act.activity_result,
                    'category': act.category1,
                    'date': act.created_at.strftime('%d %b %Y'),
                }
                for act in recent
            ],
            'report_date': datetime.now().strftime('%d %B %Y'),
            'period_days': self.days_lookback
        }
    
    def format_whatsapp_message(self, report: Dict) -> str:
        """
        Format report as WhatsApp message
        Args:
            report: Report dict from generate_child_report
        Returns:
            str: Formatted WhatsApp message
        """
        message = f"""
*Relaváu Atividade Estudante* 📚

Olá {report['parent_name']},

Nia Atualizasaun ba {report['child_name']} ({report['age_group']})

*Período:* Últimos {report['period_days']} diás ({report['report_date']})

📊 *Resulta Prinsipál:*
• Total Atividade: {report['total_activities']}
• Atinji Rezultadu: {report['achieved_activities']}
• Taxa Atinji: {report['achievement_rate']}%

{"🎯 *Tópiku Prinsipál:*" if report['themes'] else ""}
{"".join([f"\n• {theme['category1']}: {theme['count']} atividade" for theme in report['themes'][:3]]) if report['themes'] else ""}

{"📝 *Atividade Resente:*" if report['recent_activities'] else ""}
{"".join([f"\n• {act['name']} - {act['result']}" for act in report['recent_activities'][:3]]) if report['recent_activities'] else ""}

Para informasaun detalhádu, haree iha portal HAAP.

Obrigádu! 🌟
---
Sistema HAAP"""
        return message.strip()
    
    def generate_all_children_reports(self, parent: Optional[User] = None) -> List[dict]:
        """
        Generate reports for all children (or a specific parent's children)
        Args:
            parent: Optional User instance. If provided, only their children are included
        Returns:
            list: List of report dicts
        """
        if parent:
            children = Child.objects.filter(parent=parent)
        else:
            children = Child.objects.filter(parent__role='parent')
        
        reports = []
        for child in children:
            try:
                report = self.generate_child_report(child)
                reports.append(report)
            except Exception as e:
                print(f"Error generating report for child {child.id}: {str(e)}")
        
        return reports


def get_report_generator(days: int = 30) -> ChildReportGenerator:
    """Factory function to create report generator"""
    return ChildReportGenerator(days_lookback=days)
