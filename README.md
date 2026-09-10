# 🤖 AI-Powered Skill Intelligence and Career Recommendation System

An AI-powered platform designed to help students understand their current skills,
identify skill gaps, discover relevant projects, receive skill recommendations,
and track their skill development over time.

## 🚀 Overview

Students often know what they have learned but struggle to understand:

- Which skills are missing?
- Which skills should they learn next?
- Which projects match their current abilities?
- How would improving a particular skill change their opportunities?
- How is their skill level progressing over time?

This project addresses these challenges through a centralized
Student Skill Intelligence platform.

## ✨ Key Features

### 👤 Student Profile Intelligence
- Create and manage student profiles
- Track interests and career goals
- Store skill proficiency
- Upload resume evidence

### 🧠 Skill Recommendations
Analyzes the student's current skill profile and recommends
skills that could provide the greatest improvement.

### 💡 Explainable Project Recommendations
Projects are ranked based on factors such as:
- Skill matching
- Missing skills
- Content similarity
- Interest alignment
- Skill-gap penalty
- Potential growth

### 🔬 What-If Skill Simulator
Allows students to simulate improving a particular skill
and observe how that change can affect recommendations.

### 📈 Skill Evolution Tracker
Records skill assessments over time and allows students
to monitor their progress.

### 📊 Student Dashboard
Provides an overview of:
- Tracked skills
- Average proficiency
- Assessments
- Available projects
- Recommended next skills
- Project opportunities
- Recent progress

## 🏗️ System Architecture

```text
                    Student
                       │
                       ▼
               Student Profile
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
       Skills       Resume       Interests
          │            │            │
          └────────────┼────────────┘
                       ▼
               Skill Intelligence
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
   Skill Analysis   Gap Analysis   Matching
          │            │            │
          └────────────┼────────────┘
                       ▼
             Recommendation Engine
                 │           │
                 ▼           ▼
          Skill Recommendations
          Project Recommendations
                 │
                 ▼
             Student Dashboard
                 │
                 ▼
        Progress / What-If Analysis
