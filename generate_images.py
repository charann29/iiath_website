#!/usr/bin/env python3
"""
IIAT Image Generation System
Uses Google Imagen 4.0 via Gemini API to generate original images
for the IIAT (Indian Institute of Advanced Technologies) website.

Replaces all upGrad-copied images with fresh AI-generated originals.
"""

import os
import sys
import time
import json
import base64
import traceback
from pathlib import Path

from google import genai
from google.genai import types

# ============================================================
# Configuration
# ============================================================
API_KEY = "AIzaSyBJ4uWE0treqYl1Jtu_RsNKIDhAizbZNag"
MODEL = "imagen-4.0-fast-generate-001"
OUTPUT_DIR = Path("assets/new")
PROGRESS_FILE = Path("image_gen_progress.json")

# Rate limiting: Imagen API typically allows ~10 requests/minute
RATE_LIMIT_DELAY = 7  # seconds between requests
MAX_RETRIES = 3

# Common style directives
PHOTO_STYLE = "photorealistic, high resolution, professional photography, sharp detail, natural lighting"
ILLUSTRATION_STYLE = "modern flat illustration, clean vector-style, vibrant colors, professional, high resolution"
PORTRAIT_STYLE = "professional headshot portrait, studio lighting, neutral background, high resolution, photorealistic"
CARD_STYLE = "modern tech illustration, gradient background, clean design, high resolution, suitable for website card"
THUMBNAIL_STYLE = "professional photography, high resolution, vibrant colors, modern university setting"

# IIAT brand context
IIAT_CONTEXT = "Indian Institute of Advanced Technologies (IIAT), a modern technology university in Hyderabad, India"

# ============================================================
# Image Definitions: {output_path: prompt}
# ============================================================

IMAGES = {}

# ---------- CAMPUS / STUDENT PHOTOS (6) ----------
IMAGES.update({
    "campus/campus_aerial.jpg": f"Aerial drone photograph of a modern university campus in India with contemporary architecture, landscaped gardens, tree-lined walkways, multiple academic buildings with glass and concrete facades, a central courtyard, warm golden hour lighting. {PHOTO_STYLE}",

    "campus/campus_lab.jpg": f"Interior of a state-of-the-art computer science laboratory in an Indian university, rows of modern workstations with dual monitors, students coding, RGB keyboard lighting, large display screens showing code and data visualizations, clean modern interior. {PHOTO_STYLE}",

    "campus/campus_library.jpg": f"Modern university library interior with floor-to-ceiling bookshelves, collaborative study pods, students studying at sleek wooden tables, large windows with natural light, contemporary architecture with warm ambient lighting. {PHOTO_STYLE}",

    "campus/students_group.jpg": f"Diverse group of Indian university students standing together on a modern campus, wearing casual clothes, smiling confidently, holding laptops and books, green trees and modern building in background, bright daylight. {PHOTO_STYLE}",

    "campus/women.jpg": f"Group of confident young Indian women students in a modern tech university campus, working together on laptops, engaged in discussion, bright modern interior, empowering and professional atmosphere. {PHOTO_STYLE}",

    "campus/university_campus.png": f"Grand entrance of a modern Indian technology university campus, impressive architectural facade with the style of a prestigious institution, wide entrance road with landscaping, clear blue sky, warm lighting, welcoming atmosphere. {PHOTO_STYLE}",
})

# ---------- B.TECH PROGRAM CARDS (6) ----------
IMAGES.update({
    "btechprogram/aiml.jpg": f"Abstract futuristic visualization of Artificial Intelligence and Machine Learning, neural network nodes connected by glowing lines, deep learning layers, brain-circuit hybrid imagery, blue and orange gradient background. {CARD_STYLE}",

    "btechprogram/blockchain.jpg": f"Abstract visualization of FinTech and blockchain technology, interconnected digital blocks with financial symbols, cryptocurrency nodes, digital ledger chains, golden and dark blue color scheme. {CARD_STYLE}",

    "btechprogram/cloud.jpg": f"Abstract visualization of cloud computing architecture, server clusters connected to a central cloud, data streams flowing, network topology, white and blue futuristic design. {CARD_STYLE}",

    "btechprogram/cyber.jpg": f"Abstract visualization of cybersecurity with AI/ML, digital shield protecting data streams, lock icons, matrix-style code rain, threat detection neural networks, dark background with green and red highlights. {CARD_STYLE}",

    "btechprogram/quantum.jpg": f"Abstract visualization of biomedical engineering and medical robotics, robotic surgical arm, DNA helix, medical imaging scans, AI-assisted diagnostics, clean white and blue medical aesthetic. {CARD_STYLE}",

    "btechprogram/web.jpg": f"Abstract visualization of core computer science, binary code streams, algorithm flowcharts, data structures, computer architecture circuits, clean modern design with blue and white tones. {CARD_STYLE}",
})

# ---------- CAREER PATHWAY IMAGES (9) ----------
IMAGES.update({
    "MaangCareer/Academic.jpg": f"Young Indian professional studying academic textbooks and research papers at a modern desk, laptop open with academic resources, university campus visible through window. {PHOTO_STYLE}",

    "MaangCareer/Build.jpg": f"Indian tech professional building a software project, multiple monitors showing code, agile project board in background, modern office space, focused and productive atmosphere. {PHOTO_STYLE}",

    "MaangCareer/Funding.jpg": f"Indian entrepreneur presenting a startup pitch to investors in a modern conference room, presentation slides on screen, professional business setting, confident body language. {PHOTO_STYLE}",

    "MaangCareer/HigherStudies.jpg": f"Indian student in graduation cap and gown holding admission letters, modern university building in background, celebrating academic achievement, bright optimistic atmosphere. {PHOTO_STYLE}",

    "MaangCareer/Ideation.jpg": f"Indian students in a brainstorming session, whiteboard filled with ideas and sticky notes, collaborative workspace, innovative tech startup atmosphere, creative energy. {PHOTO_STYLE}",

    "MaangCareer/Researchv2.jpg": f"Indian researcher working in a modern computer science lab, analyzing data visualizations on large screens, writing research notes, academic research environment. {PHOTO_STYLE}",

    "MaangCareer/coding.jpg": f"Close-up of an Indian developer's hands typing code on a mechanical keyboard, multiple monitors showing syntax-highlighted code, dark theme IDE, modern developer workspace. {PHOTO_STYLE}",

    "MaangCareer/interview.jpg": f"Indian professional in a job interview at a tech company, sitting across from interviewers at a modern conference table, whiteboard with technical diagrams, professional and confident. {PHOTO_STYLE}",

    "MaangCareer/portfolio.jpg": f"Indian tech professional presenting their portfolio website on a large monitor, showcasing projects and achievements, modern creative workspace, warm lighting. {PHOTO_STYLE}",
})

# ---------- CURRICULUM YEAR IMAGES (15) ----------
# Year 1: Foundation
IMAGES.update({
    "curriculum/years/y1e1.jpg": f"First-year computer science students learning programming fundamentals, coding on laptops in a modern classroom, beginner-friendly collaborative environment, Indian university setting. {THUMBNAIL_STYLE}",

    "curriculum/years/y1e2.jpg": f"Mathematics and discrete structures class, Indian professor at whiteboard explaining algorithms, students taking notes, modern lecture hall with digital displays. {THUMBNAIL_STYLE}",

    "curriculum/years/y1e3.jpg": f"Physics and electronics laboratory, Indian students working with circuit boards and oscilloscopes, hands-on engineering experiments, well-equipped modern lab. {THUMBNAIL_STYLE}",

    "curriculum/years/y1e4.jpg": f"Communication skills workshop, Indian students giving presentations and participating in group discussions, modern seminar room, professional development atmosphere. {THUMBNAIL_STYLE}",
})

# Year 2: Intermediate
IMAGES.update({
    "curriculum/years/y2e1.jpg": f"Data structures and algorithms class, Indian students solving complex coding problems on whiteboards, competitive programming environment, modern computer lab. {THUMBNAIL_STYLE}",

    "curriculum/years/y2e2.jpg": f"Database management systems lab, Indian students working with SQL queries on screens, relational database diagrams on display, hands-on database design. {THUMBNAIL_STYLE}",

    "curriculum/years/y2e3.jpg": f"Operating systems and networking lab, Indian students configuring servers and network equipment, terminal windows showing Linux commands, hands-on systems learning. {THUMBNAIL_STYLE}",

    "curriculum/years/y2e4.jpg": f"Web development workshop, Indian students building websites, code editors showing HTML/CSS/JavaScript, collaborative pair programming, modern tech workspace. {THUMBNAIL_STYLE}",
})

# Year 3: Advanced
IMAGES.update({
    "curriculum/years/y3e1.jpg": f"Machine learning class, Indian students training AI models on GPU workstations, data visualizations and neural network diagrams on screens, advanced computing lab. {THUMBNAIL_STYLE}",

    "curriculum/years/y3e2.jpg": f"Software engineering and DevOps lab, Indian students working on CI/CD pipelines, Docker containers, cloud deployment dashboards, agile project management boards. {THUMBNAIL_STYLE}",

    "curriculum/years/y3e3.jpg": f"Cybersecurity and ethical hacking lab, Indian students performing penetration testing, security monitoring dashboards, dark theme terminals with security tools. {THUMBNAIL_STYLE}",

    "curriculum/years/y3e4.jpg": f"Cloud computing workshop, Indian students working with AWS/Azure dashboards, deploying microservices, serverless architecture diagrams, modern cloud infrastructure. {THUMBNAIL_STYLE}",
})

# Year 4: Specialization
IMAGES.update({
    "curriculum/years/y4e1.jpg": f"Final year capstone project presentation, Indian students demonstrating their tech project to a panel, working prototype on screen, professional presentation setting. {THUMBNAIL_STYLE}",

    "curriculum/years/y4e2.jpg": f"Industry internship scene, Indian student working at a tech company alongside senior engineers, modern corporate office, real-world software development. {THUMBNAIL_STYLE}",

    "curriculum/years/y4e3.jpg": f"Research thesis defense, Indian student presenting research findings to academic committee, academic papers and data charts on display, formal university setting. {THUMBNAIL_STYLE}",
})

# ---------- CURRICULUM PROJECT THUMBNAILS (24) ----------
IMAGES.update({
    "curriculum/project/APIGateway.png": f"Technical illustration of an API Gateway architecture, microservices connected through a central gateway node, request routing, load balancing, clean diagram style. {ILLUSTRATION_STYLE}",

    "curriculum/project/Assignment.png": f"Digital illustration of an online assignment submission platform, student dashboard with assignments, grades, and deadlines, clean UI mockup style. {ILLUSTRATION_STYLE}",

    "curriculum/project/Automated.png": f"Illustration of automated testing and CI/CD pipeline, code flowing through test stages, green checkmarks, automated build process, DevOps workflow. {ILLUSTRATION_STYLE}",

    "curriculum/project/Colloborative.png": f"Illustration of a collaborative document editing platform, multiple cursors on shared document, real-time collaboration features, team workspace. {ILLUSTRATION_STYLE}",

    "curriculum/project/Dashboard.png": f"Illustration of a data analytics dashboard, charts, graphs, KPI metrics, interactive data visualizations, modern business intelligence interface. {ILLUSTRATION_STYLE}",

    "curriculum/project/DynamicUI.png": f"Illustration of dynamic UI component library, responsive design elements, component tree, drag-and-drop interface builder, modern frontend development. {ILLUSTRATION_STYLE}",

    "curriculum/project/Flight.png": f"Illustration of a flight booking system, airplane icons, search interface, seat selection, booking flow, travel technology platform. {ILLUSTRATION_STYLE}",

    "curriculum/project/Healthcare.png": f"Illustration of a healthcare management system, patient records, medical appointment scheduling, health monitoring dashboard, medical technology. {ILLUSTRATION_STYLE}",

    "curriculum/project/Helpdesk.png": f"Illustration of a customer support helpdesk system, ticket management, chatbot interface, support agent dashboard, customer service technology. {ILLUSTRATION_STYLE}",

    "curriculum/project/Monitoring.png": f"Illustration of a system monitoring dashboard, server health metrics, CPU/memory graphs, alert notifications, infrastructure monitoring. {ILLUSTRATION_STYLE}",

    "curriculum/project/Multi-Language.png": f"Illustration of a multi-language translation platform, language flags, text translation interface, NLP processing, internationalization. {ILLUSTRATION_STYLE}",

    "curriculum/project/Multi-Tenant.png": f"Illustration of multi-tenant SaaS architecture, isolated tenant data, shared infrastructure, tenant management dashboard, cloud platform. {ILLUSTRATION_STYLE}",

    "curriculum/project/Navigation.png": f"Illustration of a GPS navigation and mapping application, route planning, real-time traffic, location pins, interactive map interface. {ILLUSTRATION_STYLE}",

    "curriculum/project/Payment.png": f"Illustration of a secure payment processing system, credit card transactions, payment gateway, encryption locks, fintech infrastructure. {ILLUSTRATION_STYLE}",

    "curriculum/project/Recognition.png": f"Illustration of an image recognition AI system, computer vision, object detection bounding boxes, facial recognition, neural network processing. {ILLUSTRATION_STYLE}",

    "curriculum/project/Student.png": f"Illustration of a student information management system, student profiles, enrollment dashboard, academic records, education technology platform. {ILLUSTRATION_STYLE}",

    "curriculum/project/WEBRTC.png": f"Illustration of a WebRTC video conferencing platform, video call interface, screen sharing, peer-to-peer connection, real-time communication. {ILLUSTRATION_STYLE}",

    "curriculum/project/cloud.png": f"Illustration of cloud storage and computing infrastructure, cloud servers, data upload/download, distributed computing, scalable architecture. {ILLUSTRATION_STYLE}",

    "curriculum/project/creditcard.png": f"Illustration of a credit card fraud detection system, transaction analysis, anomaly detection alerts, secure banking, AI-powered fraud prevention. {ILLUSTRATION_STYLE}",

    "curriculum/project/fraud.png": f"Illustration of a financial fraud detection system, suspicious transaction patterns, machine learning classification, risk scoring, security analytics. {ILLUSTRATION_STYLE}",

    "curriculum/project/parking.png": f"Illustration of a smart parking management system, parking lot sensors, occupancy display, automated parking, IoT-connected infrastructure. {ILLUSTRATION_STYLE}",

    "curriculum/project/personalized.png": f"Illustration of a personalized recommendation engine, user preferences, content suggestions, machine learning algorithms, personalization technology. {ILLUSTRATION_STYLE}",

    "curriculum/project/supplychain.png": f"Illustration of a supply chain management system, logistics tracking, inventory management, warehouse operations, supply chain analytics. {ILLUSTRATION_STYLE}",

    "curriculum/project/waste.png": f"Illustration of a smart waste management system, IoT-enabled waste bins, collection route optimization, recycling sorting, green technology. {ILLUSTRATION_STYLE}",
})

# ---------- LBC THUMBNAILS (23) ----------
IMAGES.update({
    "LBCthumbnail/advanced.jpg": f"Advanced technology workshop at an Indian university, students working with cutting-edge equipment, robotics and AI demonstrations, futuristic learning environment. {THUMBNAIL_STYLE}",

    "LBCthumbnail/campus.jpg": f"Beautiful Indian university campus during golden hour, students walking on tree-lined paths, modern architecture, vibrant campus life. {THUMBNAIL_STYLE}",

    "LBCthumbnail/communication.jpg": f"Indian students practicing public speaking and communication skills, podium presentation, engaged audience, modern auditorium, confident speakers. {THUMBNAIL_STYLE}",

    "LBCthumbnail/compete.jpg": f"Indian students participating in a coding hackathon competition, intense coding on laptops, team collaboration, countdown timer on screen, competitive energy. {THUMBNAIL_STYLE}",

    "LBCthumbnail/continuous.jpg": f"Indian student engaged in continuous learning, studying on tablet and laptop simultaneously, online courses on screen, self-paced learning, modern study space. {THUMBNAIL_STYLE}",

    "LBCthumbnail/culture.jpg": f"Cultural festival at an Indian university, students performing traditional dances, colorful decorations, multicultural celebration, vibrant campus event. {THUMBNAIL_STYLE}",

    "LBCthumbnail/data.jpg": f"Indian students analyzing data on large screens, data science workshop, statistical visualizations, collaborative data analysis, modern analytics lab. {THUMBNAIL_STYLE}",

    "LBCthumbnail/debate.jpg": f"Indian students in a formal debate competition, speakers at podiums, judges panel, engaged audience, modern auditorium, intellectual discourse. {THUMBNAIL_STYLE}",

    "LBCthumbnail/design.jpg": f"Indian students in a UI/UX design thinking workshop, sketching wireframes, prototyping on tablets, design tools on screens, creative studio atmosphere. {THUMBNAIL_STYLE}",

    "LBCthumbnail/idea.jpg": f"Indian students in an ideation session, brainstorming with sticky notes on glass walls, lightbulb moment, innovative thinking, modern co-working space. {THUMBNAIL_STYLE}",

    "LBCthumbnail/industry.jpg": f"Industry professionals visiting an Indian university, guest lecture by tech CEO, students networking with industry leaders, corporate-academic partnership. {THUMBNAIL_STYLE}",

    "LBCthumbnail/innovation.jpg": f"Innovation lab at an Indian university, students building prototypes, 3D printers and electronics workbenches, maker space, hands-on innovation. {THUMBNAIL_STYLE}",

    "LBCthumbnail/integration.jpg": f"Indian students working on system integration projects, connecting multiple APIs and services, large screens showing architecture diagrams, collaborative coding. {THUMBNAIL_STYLE}",

    "LBCthumbnail/leadership.jpg": f"Indian student leaders organizing a campus event, team coordination, leadership workshop, student council meeting, confident young leaders. {THUMBNAIL_STYLE}",

    "LBCthumbnail/pitch.jpg": f"Indian students pitching their startup idea, presentation to investor panel, business plan on screen, entrepreneurship competition, shark-tank style event. {THUMBNAIL_STYLE}",

    "LBCthumbnail/prepare.jpg": f"Indian students preparing for placement interviews, mock interview practice, resume review session, career preparation workshop, professional guidance. {THUMBNAIL_STYLE}",

    "LBCthumbnail/problem.jpg": f"Indian students solving complex problems on whiteboards, algorithmic thinking, mathematical equations, problem-solving competition, intellectual challenge. {THUMBNAIL_STYLE}",

    "LBCthumbnail/professional.jpg": f"Indian students in professional attire at a corporate networking event, exchanging business cards, professional development, industry meetup. {THUMBNAIL_STYLE}",

    "LBCthumbnail/scale.jpg": f"Indian students working on scalable software architecture, cloud deployment screens, microservices diagrams, load testing dashboards, enterprise-level development. {THUMBNAIL_STYLE}",

    "LBCthumbnail/showcase.jpg": f"Project showcase exhibition at an Indian university, students demonstrating tech projects to visitors, demo booths with displays, science fair atmosphere. {THUMBNAIL_STYLE}",

    "LBCthumbnail/startegic.jpg": f"Indian students in a strategic planning session, SWOT analysis on whiteboard, business strategy discussion, management workshop, analytical thinking. {THUMBNAIL_STYLE}",

    "LBCthumbnail/thesis.jpg": f"Indian student working on their thesis, surrounded by research papers, laptop with academic writing, deep concentration, university library setting. {THUMBNAIL_STYLE}",

    "LBCthumbnail/writing.jpg": f"Indian students in a technical writing workshop, drafting documentation, academic paper writing, collaborative editing, modern classroom with laptops. {THUMBNAIL_STYLE}",
})

# ---------- SCHOLARSHIP IMAGES (3) ----------
IMAGES.update({
    "scholarships/need_based.jpg": f"Heartwarming scene of a deserving Indian student receiving a scholarship certificate, family looking proud, modern university ceremony, hope and opportunity, warm lighting. {PHOTO_STYLE}",

    "scholarships/merit_based.jpg": f"Brilliant Indian student receiving a merit scholarship award on stage, trophy and certificate, academic excellence celebration, university convocation hall, pride and achievement. {PHOTO_STYLE}",

    "scholarships/innovation_scholarship.jpg": f"Indian student inventor showcasing an innovative tech project, winning an innovation scholarship, judges impressed, prototype demonstration, entrepreneurial spirit. {PHOTO_STYLE}",
})

# ---------- FOUNDER PHOTOS (6) ----------
# 3 portrait + 3 landscape versions
IMAGES.update({
    "founders/Founder1.png": f"Professional portrait of an Indian male technology executive in his 50s, wearing a formal dark suit, confident smile, modern office background, corporate headshot style, warm professional lighting. {PORTRAIT_STYLE}",

    "founders/Founder2.png": f"Professional portrait of an Indian female technology leader in her 40s, wearing elegant business attire, approachable confident expression, modern minimalist background, executive headshot. {PORTRAIT_STYLE}",

    "founders/Founder3.png": f"Professional portrait of an Indian male academic leader in his 60s, wearing formal attire with reading glasses, wise and distinguished appearance, university setting background, scholarly portrait. {PORTRAIT_STYLE}",

    "founders/LFounder1.png": f"Indian male technology executive in his 50s speaking at a conference, standing at podium, large screen behind showing tech presentation, professional event photography, leadership in action. {PHOTO_STYLE}",

    "founders/LFounder2.png": f"Indian female technology leader in her 40s leading a boardroom meeting, gesturing while presenting to colleagues, modern corporate setting, dynamic leadership photography. {PHOTO_STYLE}",

    "founders/LFounder3.png": f"Indian male academic leader in his 60s inaugurating a new university building, ribbon cutting ceremony, dignitaries around, formal university event, distinguished leadership. {PHOTO_STYLE}",
})

# ---------- MENTOR HEADSHOTS (18) ----------
MENTOR_NAMES = [
    ("Ajeyav1", "young Indian male software engineer, mid-20s, casual tech company attire"),
    ("Ananthv1", "Indian male data scientist, early 30s, smart casual, friendly expression"),
    ("Divyanshv1", "Indian male AI researcher, late 20s, modern professional look, glasses"),
    ("Gladden_Rumao", "Indian male senior developer, mid-30s, confident smile, business casual"),
    ("MAHESWARARAOv1", "Indian male professor, late 40s, formal academic attire, distinguished"),
    ("Mithunv1", "Indian male tech lead, early 30s, polo shirt, approachable expression"),
    ("Raghavv1", "Indian male cloud architect, late 20s, modern professional attire"),
    ("Rishab_Bafna", "Indian male product manager, early 30s, business casual, confident"),
    ("Shaharv1", "Indian male cybersecurity expert, mid-30s, serious professional look"),
    ("Shreyanshv1", "Indian male full-stack developer, mid-20s, casual tech startup style"),
    ("Shubhamv1", "Indian male ML engineer, late 20s, smart casual, enthusiastic expression"),
    ("Sourovv1", "Indian male DevOps engineer, early 30s, casual professional, friendly"),
    ("Vivekv1", "Indian male blockchain developer, late 20s, modern tech style"),
    ("jyotiv1", "Indian female software engineer, mid-20s, professional attire, confident smile"),
    ("rishiv1", "Indian male backend developer, early 30s, casual professional look"),
    ("shivamv1", "Indian male frontend developer, mid-20s, trendy tech startup attire"),
    ("vishwav1", "Indian male systems architect, mid-30s, business formal, experienced look"),
    ("yaminiv1", "Indian female data analyst, late 20s, professional attire, warm smile"),
]

for name, desc in MENTOR_NAMES:
    IMAGES[f"mentors/{name}.png"] = f"Professional headshot portrait photograph of a {desc}, studio lighting, neutral gradient background, high-quality corporate portrait photography, sharp focus, natural skin tones. {PORTRAIT_STYLE}"

# ---------- AWARD IMAGES (8) ----------
IMAGES.update({
    "awards/ab_award.png": f"Prestigious technology education excellence award trophy, crystal and gold design, engraved with 'Excellence in Technology Education', professional product photography, dark background with dramatic lighting. {PHOTO_STYLE}",

    "awards/brandon_hall_award.png": f"Gold excellence award for learning and development, elegant trophy design with laurel wreath, engraved plaque, professional award photography, dark velvet background. {PHOTO_STYLE}",

    "awards/bw.jpg": f"Business excellence award trophy, modern geometric crystal design, corporate achievement recognition, professional product photography, gradient dark background. {PHOTO_STYLE}",

    "awards/et_awards.png": f"Education technology innovation award, sleek modern trophy with digital circuit pattern, 'Innovation in EdTech' engraving, professional studio photography, dark elegant background. {PHOTO_STYLE}",

    "awards/ft_award.png": f"Future of technology education award, futuristic trophy design with LED elements, modern materials, technology excellence recognition, dramatic studio lighting. {PHOTO_STYLE}",

    "awards/hurun_india_award.png": f"India's most valued education brand award, elegant gold and marble trophy, prestigious recognition for educational excellence, luxury award photography. {PHOTO_STYLE}",

    "awards/mosaic_award.png": f"Diversity and inclusion award in education, colorful mosaic-patterned trophy, celebrating multicultural excellence, vibrant and artistic award design, studio photography. {PHOTO_STYLE}",

    "awards/youtube_award.png": f"Digital content excellence award for education, modern trophy with play button design element, digital education achievement, sleek metallic finish, professional photography. {PHOTO_STYLE}",
})


def load_progress():
    """Load progress from previous runs."""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"completed": [], "failed": []}


def save_progress(progress):
    """Save progress for resume capability."""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)


def generate_image(client, prompt, output_path, retries=MAX_RETRIES):
    """Generate a single image using Imagen 4.0."""
    for attempt in range(retries):
        try:
            response = client.models.generate_images(
                model=MODEL,
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    output_mime_type='image/png',
                    aspect_ratio='16:9' if any(kw in str(output_path) for kw in ['campus', 'MaangCareer', 'LBC', 'scholarship', 'LFounder', 'curriculum/years']) else '1:1',
                )
            )

            if response.generated_images:
                img_data = response.generated_images[0].image.image_bytes
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'wb') as f:
                    f.write(img_data)
                return True, len(img_data)
            else:
                print(f"    WARNING: No image generated (attempt {attempt + 1})")
                if attempt < retries - 1:
                    time.sleep(5)

        except Exception as e:
            error_msg = str(e)
            print(f"    ERROR (attempt {attempt + 1}/{retries}): {error_msg[:120]}")
            if "429" in error_msg or "quota" in error_msg.lower() or "rate" in error_msg.lower():
                wait = 30 * (attempt + 1)
                print(f"    Rate limited. Waiting {wait}s...")
                time.sleep(wait)
            elif "safety" in error_msg.lower() or "blocked" in error_msg.lower():
                print(f"    Content blocked by safety filter. Skipping.")
                return False, 0
            elif attempt < retries - 1:
                time.sleep(10)

    return False, 0


def main():
    # Parse arguments
    category_filter = None
    if len(sys.argv) > 1:
        category_filter = sys.argv[1]
        print(f"Filtering to category: {category_filter}")

    client = genai.Client(api_key=API_KEY)
    progress = load_progress()
    completed = set(progress["completed"])

    # Filter images based on category if specified
    images_to_generate = {}
    for path, prompt in IMAGES.items():
        if category_filter:
            if not path.startswith(category_filter):
                continue
        if path not in completed:
            images_to_generate[path] = prompt

    total = len(images_to_generate)
    already_done = len([p for p in IMAGES if p in completed and (not category_filter or p.startswith(category_filter))])

    print(f"=" * 60)
    print(f"IIAT Image Generation System")
    print(f"=" * 60)
    print(f"Total images defined: {len(IMAGES)}")
    print(f"Already completed: {already_done}")
    print(f"To generate: {total}")
    print(f"Rate limit delay: {RATE_LIMIT_DELAY}s between requests")
    est_time = total * RATE_LIMIT_DELAY
    print(f"Estimated time: ~{est_time // 60}m {est_time % 60}s")
    print(f"=" * 60)

    if total == 0:
        print("Nothing to generate. All done!")
        return

    generated = 0
    failed = 0

    for idx, (rel_path, prompt) in enumerate(images_to_generate.items(), 1):
        output_path = OUTPUT_DIR / rel_path
        print(f"\n[{idx}/{total}] Generating: {rel_path}")
        print(f"  Prompt: {prompt[:80]}...")

        success, size = generate_image(client, prompt, output_path)

        if success:
            generated += 1
            completed.add(rel_path)
            progress["completed"] = list(completed)
            save_progress(progress)
            print(f"  DONE: {size / 1024:.0f} KB -> {output_path}")
        else:
            failed += 1
            if rel_path not in progress["failed"]:
                progress["failed"].append(rel_path)
            save_progress(progress)
            print(f"  FAILED: {rel_path}")

        # Rate limiting
        if idx < total:
            print(f"  Waiting {RATE_LIMIT_DELAY}s (rate limit)...")
            time.sleep(RATE_LIMIT_DELAY)

    print(f"\n{'=' * 60}")
    print(f"Generation complete!")
    print(f"  Generated: {generated}")
    print(f"  Failed: {failed}")
    print(f"  Total completed (all runs): {len(completed)}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
