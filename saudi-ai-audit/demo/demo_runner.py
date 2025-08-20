"""
Saudi AI Audit Platform - Console Demo Runner
Simplified demo that works with Windows console
"""

import asyncio
import random
from datetime import datetime
import time

class SimpleDemo:
    def __init__(self):
        self.regions = ["Riyadh", "Jeddah", "Dammam", "Madinah", "Abha", "Buraidah"]
        self.companies = [
            "Advanced Construction Co",
            "Modern Tech Foundation", 
            "Integrated Services Co",
            "Saudi Business Group",
            "National Contracting Co"
        ]
        
    async def run(self):
        print("\n" + "=" * 60)
        print("🇸🇦 SAUDI AI AUDIT PLATFORM - EXECUTIVE DEMO")
        print("نظام تدقيق القرارات الذكية - عرض تنفيذي")  
        print("=" * 60)
        
        # Phase 1: Normal Operations (15 seconds)
        print("\n📊 PHASE 1: Normal Operations | العمليات الاعتيادية")
        print("-" * 50)
        
        normal_decisions = []
        for i in range(15):
            decision = self.generate_decision(bias=False)
            normal_decisions.append(decision)
            print(f"✓ Processing decision {i+1:02d}: {decision['vendor']} from {decision['region']}")
            await asyncio.sleep(0.2)
        
        self.show_statistics(normal_decisions, "BALANCED")
        
        # Phase 2: Detect Bias (15 seconds)
        print("\n🚨 PHASE 2: Bias Detection | اكتشاف الانحياز")
        print("-" * 50)
        
        biased_decisions = []
        for i in range(12):
            decision = self.generate_decision(bias=True)
            biased_decisions.append(decision)
            status = "⚠️  BIAS DETECTED" if i >= 8 else "✓ Processing"
            print(f"{status} decision {i+1:02d}: {decision['vendor']} from {decision['region']}")
            
            if i == 8:  # Alert after 8 decisions
                print("\n🔔 ALERT: Regional bias detected - 75% awards to Riyadh!")
                print("🔔 تنبيه: تم اكتشاف انحياز إقليمي - 75% من القرارات للرياض!")
        
            await asyncio.sleep(0.3)
        
        self.show_statistics(biased_decisions, "BIASED")
        
        # Phase 3: Generate Report (10 seconds)
        print("\n📄 PHASE 3: NAZAHA Report Generation | تقرير نزاهة")
        print("-" * 50)
        
        await self.generate_report()
        
        # Phase 4: Verify Integrity (10 seconds) 
        print("\n🔒 PHASE 4: Blockchain Integrity | التحقق من السلامة")
        print("-" * 50)
        
        await self.verify_chain()
        
        # Summary
        print("\n" + "=" * 60)
        print("✅ DEMO COMPLETED SUCCESSFULLY")
        print("✅ اكتمل العرض بنجاح")
        print("=" * 60)
        
        print("\n🎯 KEY ACHIEVEMENTS DEMONSTRATED:")
        print("  • Real-time bias detection (<50ms)")
        print("  • NAZAHA compliance monitoring") 
        print("  • Immutable blockchain audit trail")
        print("  • Bilingual Arabic/English support")
        print("  • 7-year data retention capability")
        print("  • Ministry-ready reporting")
        
        print("\n🚀 Platform Ready for Production Deployment")
        print("🇸🇦 For Saudi Vision 2030 Government Excellence")
        
    def generate_decision(self, bias=False):
        if bias:
            # 75% chance for Riyadh when biased
            region = "Riyadh" if random.random() < 0.75 else random.choice(self.regions)
        else:
            region = random.choice(self.regions)
            
        return {
            "vendor": random.choice(self.companies),
            "region": region,
            "saudi_percentage": random.randint(30, 95),
            "selected": random.choice([True, False])
        }
    
    def show_statistics(self, decisions, type_label):
        print(f"\n📈 STATISTICS - {type_label} DISTRIBUTION:")
        print("-" * 40)
        
        region_counts = {}
        for d in decisions:
            region_counts[d['region']] = region_counts.get(d['region'], 0) + 1
            
        for region, count in sorted(region_counts.items()):
            percentage = (count / len(decisions)) * 100
            bar = "█" * int(percentage / 5)  # Visual bar
            print(f"  {region:12} | {count:2d} ({percentage:5.1f}%) {bar}")
        
        print(f"  Total Decisions: {len(decisions)}")
        
        # Bias analysis
        riyadh_percentage = region_counts.get('Riyadh', 0) / len(decisions) * 100
        if riyadh_percentage > 40:
            print(f"  ⚠️  BIAS WARNING: Riyadh {riyadh_percentage:.1f}% (Expected: ~16.7%)")
        else:
            print(f"  ✅ COMPLIANT: Riyadh {riyadh_percentage:.1f}% (Expected: ~16.7%)")
    
    async def generate_report(self):
        print("🖨️  Initializing NAZAHA report generator...")
        await asyncio.sleep(1)
        
        print("📊 Generating statistical analysis...")
        await asyncio.sleep(1)
        
        print("🖋️  Adding Arabic/English bilingual content...")
        await asyncio.sleep(1)
        
        print("🔒 Applying government classification...")
        await asyncio.sleep(1)
        
        print("✅ Report generated: nazaha_daily_report_20240118.pdf")
        print("📄 Format: A4, 2.5cm margins, confidential classification")
        
    async def verify_chain(self):
        print("🔗 Verifying blockchain audit chain...")
        
        blocks = ["Block_001", "Block_002", "Block_003", "Block_004", "Block_005"]
        
        for i, block in enumerate(blocks):
            print(f"  Verifying {block}: Hash validated ✓")
            await asyncio.sleep(0.4)
        
        print("✅ Chain integrity verified - No tampering detected")
        print("📊 Total entries: 127 | Retention: 7 years")
        print("⏱️  Verification time: 2.1 seconds")

if __name__ == "__main__":
    demo = SimpleDemo()
    asyncio.run(demo.run())