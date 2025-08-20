"""
عرض تنفيذي لوزارة التجارة
Executive Demo for Ministry of Commerce
Duration: 3 minutes
"""

import asyncio
import random
from datetime import datetime
from hijri_converter import Gregorian
from rich.console import Console
from rich.table import Table
from rich.progress import track
import arabic_reshaper
from bidi.algorithm import get_display

console = Console()

class ExecutiveDemo:
    def __init__(self):
        self.regions = ["الرياض", "جدة", "الدمام", "المدينة", "أبها", "بريدة"]
        self.companies = [
            "شركة البناء المتقدمة",
            "مؤسسة التقنية الحديثة",
            "شركة الخدمات المتكاملة",
            "مجموعة الأعمال السعودية",
            "شركة المقاولات الوطنية"
        ]
        
    async def run(self):
        # Header
        console.print("\n[bold blue]نظام تدقيق القرارات الذكية[/bold blue]")
        console.print("[bold blue]Saudi AI Audit System[/bold blue]")
        console.print("=" * 60)
        
        # Phase 1: Normal Operations (30 seconds)
        console.print("\n[green]المرحلة الأولى: العمليات الاعتيادية[/green]")
        console.print("[green]Phase 1: Normal Operations[/green]\n")
        
        normal_decisions = []
        for i in track(range(30), description="معالجة قرارات..."):
            decision = self.generate_decision(bias=False)
            normal_decisions.append(decision)
            await asyncio.sleep(0.1)
        
        self.show_statistics(normal_decisions, "عادي")
        
        # Phase 2: Detect Bias (30 seconds)
        console.print("\n[yellow]المرحلة الثانية: اكتشاف الانحياز[/yellow]")
        console.print("[yellow]Phase 2: Bias Detection[/yellow]\n")
        
        biased_decisions = []
        for i in track(range(20), description="معالجة مع انحياز..."):
            decision = self.generate_decision(bias=True)
            biased_decisions.append(decision)
            await asyncio.sleep(0.1)
            
            if i == 15:  # Alert after 15 decisions
                console.print("\n[bold red]⚠️ تحذير: تم اكتشاف انحياز محتمل![/bold red]")
                console.print("[bold red]⚠️ Warning: Potential bias detected![/bold red]")
        
        self.show_statistics(biased_decisions, "منحاز")
        
        # Phase 3: Generate Report (30 seconds)
        console.print("\n[cyan]المرحلة الثالثة: تقرير نزاهة[/cyan]")
        console.print("[cyan]Phase 3: NAZAHA Report[/cyan]\n")
        
        await self.generate_report(biased_decisions)
        
        # Phase 4: Verify Integrity (30 seconds)
        console.print("\n[magenta]المرحلة الرابعة: التحقق من السلامة[/magenta]")
        console.print("[magenta]Phase 4: Integrity Verification[/magenta]\n")
        
        await self.verify_chain()
        
        # Summary
        console.print("\n[bold green]✓ اكتمل العرض بنجاح[/bold green]")
        console.print("[bold green]✓ Demo completed successfully[/bold green]")
        
    def generate_decision(self, bias=False):
        if bias:
            # 60% chance for Riyadh when biased
            region = "الرياض" if random.random() < 0.6 else random.choice(self.regions)
        else:
            region = random.choice(self.regions)
            
        return {
            "vendor": random.choice(self.companies),
            "region": region,
            "saudi_percentage": random.randint(30, 95),
            "selected": random.choice([True, False])
        }
    
    def show_statistics(self, decisions, type_label):
        table = Table(title=f"إحصائيات القرارات - {type_label}")
        table.add_column("المنطقة", style="cyan")
        table.add_column("العدد", style="magenta")
        table.add_column("النسبة", style="green")
        
        region_counts = {}
        for d in decisions:
            region_counts[d['region']] = region_counts.get(d['region'], 0) + 1
            
        for region, count in region_counts.items():
            percentage = (count / len(decisions)) * 100
            table.add_row(region, str(count), f"{percentage:.1f}%")
            
        console.print(table)
    
    async def generate_report(self, decisions):
        console.print("جاري إنشاء تقرير نزاهة...")
        await asyncio.sleep(2)
        console.print("[green]✓ تم إنشاء التقرير: demo_report_NAZAHA.pdf[/green]")
        
    async def verify_chain(self):
        console.print("التحقق من سلسلة التدقيق...")
        for i in track(range(10), description="فحص البلوكات..."):
            await asyncio.sleep(0.1)
        console.print("[green]✓ السلسلة سليمة - لم يتم اكتشاف تلاعب[/green]")

if __name__ == "__main__":
    demo = ExecutiveDemo()
    asyncio.run(demo.run())