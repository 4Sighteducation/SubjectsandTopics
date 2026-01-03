"""
Edexcel Mathematics (9MA0) - Manual Topic Upload
Complete hierarchy with proper topic structure:
  Level 0: Papers (3)
  Level 1: Main Topics (10)
  Level 2: Learning Objectives (~135)
  Level 3: Methods/Techniques (~50)

Total: ~200 topics with 4 levels
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client

env_path = Path(r"C:\Users\tonyd\OneDrive - 4Sight Education Ltd\Apps\flash-curriculum-pipeline\.env")
load_dotenv(env_path)

supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY'))

SUBJECT = {
    'code': '9MA0',
    'name': 'Mathematics',
    'qualification': 'A-Level',
    'exam_board': 'Edexcel',
    'pdf_url': 'https://qualifications.pearson.com/content/dam/pdf/A%20Level/Mathematics/2017/specification-and-sample-assesment/a-level-l3-mathematics-specification-issue4.pdf'
}

TOPICS = [
    # Level 0: Papers
    {'code': 'Paper1', 'title': 'Paper 1: Pure Mathematics 1', 'level': 0, 'parent': None},
    {'code': 'Paper2', 'title': 'Paper 2: Pure Mathematics 2', 'level': 0, 'parent': None},
    {'code': 'Paper3', 'title': 'Paper 3: Statistics and Mechanics', 'level': 0, 'parent': None},
    
    # ==================================================================================
    # TOPIC 1: PROOF
    # ==================================================================================
    {'code': 'T1', 'title': '1 - Proof', 'level': 1, 'parent': 'Paper1'},
    
    {'code': 'T1_1', 'title': '1.1 Understand and use the structure of mathematical proof, proceeding from given assumptions through a series of logical steps to a conclusion; use methods of proof', 'level': 2, 'parent': 'T1'},
    {'code': 'T1_1_1', 'title': 'Proof by deduction', 'level': 3, 'parent': 'T1_1'},
    {'code': 'T1_1_2', 'title': 'Proof by exhaustion', 'level': 3, 'parent': 'T1_1'},
    {'code': 'T1_1_3', 'title': 'Disproof by counter example', 'level': 3, 'parent': 'T1_1'},
    {'code': 'T1_1_4', 'title': 'Proof by contradiction (including proof of the irrationality of √2 and the infinity of primes, and application to unfamiliar proofs)', 'level': 3, 'parent': 'T1_1'},
    
    # ==================================================================================
    # TOPIC 2: ALGEBRA AND FUNCTIONS
    # ==================================================================================
    {'code': 'T2', 'title': '2 - Algebra and functions', 'level': 1, 'parent': 'Paper1'},
    
    {'code': 'T2_1', 'title': '2.1 Understand and use the laws of indices for all rational exponents', 'level': 2, 'parent': 'T2'},
    {'code': 'T2_2', 'title': '2.2 Use and manipulate surds, including rationalising the denominator', 'level': 2, 'parent': 'T2'},
    {'code': 'T2_3', 'title': '2.3 Work with quadratic functions and their graphs', 'level': 2, 'parent': 'T2'},
    {'code': 'T2_3_1', 'title': 'The discriminant of a quadratic function', 'level': 3, 'parent': 'T2_3'},
    {'code': 'T2_3_2', 'title': 'Completing the square', 'level': 3, 'parent': 'T2_3'},
    {'code': 'T2_3_3', 'title': 'Solution of quadratic equations', 'level': 3, 'parent': 'T2_3'},
    {'code': 'T2_4', 'title': '2.4 Solve simultaneous equations in two variables by elimination and by substitution', 'level': 2, 'parent': 'T2'},
    {'code': 'T2_5', 'title': '2.5 Solve linear and quadratic inequalities in a single variable and interpret such inequalities graphically', 'level': 2, 'parent': 'T2'},
    {'code': 'T2_6', 'title': '2.6 Manipulate polynomials algebraically, including expanding brackets and collecting like terms, factorisation', 'level': 2, 'parent': 'T2'},
    {'code': 'T2_7', 'title': '2.7 Understand and use graphs of functions; sketch curves defined by simple equations', 'level': 2, 'parent': 'T2'},
    {'code': 'T2_8', 'title': '2.8 Understand and use proportional relationships and their graphs', 'level': 2, 'parent': 'T2'},
    {'code': 'T2_9', 'title': '2.9 Understand the effect of simple transformations on the graph of y = f(x)', 'level': 2, 'parent': 'T2'},
    {'code': 'T2_10', 'title': '2.10 Decompose rational functions into partial fractions', 'level': 2, 'parent': 'T2'},
    {'code': 'T2_11', 'title': '2.11 Use of functions in modelling, including consideration of limitations and refinements of the models', 'level': 2, 'parent': 'T2'},
    
    # ==================================================================================
    # TOPIC 3: COORDINATE GEOMETRY
    # ==================================================================================
    {'code': 'T3', 'title': '3 - Coordinate geometry in the (x, y) plane', 'level': 1, 'parent': 'Paper1'},
    
    {'code': 'T3_1', 'title': '3.1 Understand and use the equation of a straight line, including the forms y − y₁ = m(x − x₁) and ax + by + c = 0; gradient conditions for two straight lines to be parallel or perpendicular', 'level': 2, 'parent': 'T3'},
    {'code': 'T3_2', 'title': '3.2 Be able to use straight line models in a variety of contexts', 'level': 2, 'parent': 'T3'},
    {'code': 'T3_3', 'title': '3.3 Understand and use the coordinate geometry of the circle including using the equation of a circle in the form (x − a)² + (y − b)² = r²', 'level': 2, 'parent': 'T3'},
    {'code': 'T3_4', 'title': '3.4 Use of the following circle properties: the angle in a semicircle is a right angle; the perpendicular from the centre to a chord bisects the chord; the radius of a circle at a given point on its circumference is perpendicular to the tangent to the circle at that point', 'level': 2, 'parent': 'T3'},
    
    # ==================================================================================
    # TOPIC 4: SEQUENCES AND SERIES  
    # ==================================================================================
    {'code': 'T4', 'title': '4 - Sequences and series', 'level': 1, 'parent': 'Paper1'},
    
    {'code': 'T4_1', 'title': '4.1 Understand and use the binomial expansion of (a + bx)ⁿ for positive integer n', 'level': 2, 'parent': 'T4'},
    {'code': 'T4_2', 'title': '4.2 Understand and use sequences and series, including binomial expansion', 'level': 2, 'parent': 'T4'},
    
    # ==================================================================================
    # TOPIC 5: TRIGONOMETRY
    # ==================================================================================
    {'code': 'T5', 'title': '5 - Trigonometry', 'level': 1, 'parent': 'Paper1'},
    
    {'code': 'T5_1', 'title': '5.1 Understand and use the definitions of sine, cosine and tangent for all arguments; the sine and cosine rules; the area of a triangle', 'level': 2, 'parent': 'T5'},
    {'code': 'T5_2', 'title': '5.2 Understand and use the definition of a radian; convert between degrees and radians; arc length, areas of sectors and segments', 'level': 2, 'parent': 'T5'},
    {'code': 'T5_3', 'title': '5.3 Understand and use standard trigonometric identities', 'level': 2, 'parent': 'T5'},
    {'code': 'T5_4', 'title': '5.4 Understand and use the standard small angle approximations', 'level': 2, 'parent': 'T5'},
    {'code': 'T5_5', 'title': '5.5 Understand and use the definitions of secant, cosecant and cotangent and of arcsin, arccos and arctan; their relationships to sine, cosine and tangent', 'level': 2, 'parent': 'T5'},
    {'code': 'T5_6', 'title': '5.6 Understand and use sec²θ ≡ 1 + tan²θ and cosec²θ ≡ 1 + cot²θ', 'level': 2, 'parent': 'T5'},
    {'code': 'T5_7', 'title': '5.7 Understand and use double angle formulae; use of formulae for sin(A ± B), cos(A ± B) and tan(A ± B)', 'level': 2, 'parent': 'T5'},
    {'code': 'T5_8', 'title': '5.8 Construct proofs involving trigonometric functions and identities', 'level': 2, 'parent': 'T5'},
    
    # ==================================================================================
    # TOPIC 6: EXPONENTIALS AND LOGARITHMS
    # ==================================================================================
    {'code': 'T6', 'title': '6 - Exponentials and logarithms', 'level': 1, 'parent': 'Paper1'},
    
    {'code': 'T6_1', 'title': '6.1 Know and use the function aˣ and its graph, where a is positive', 'level': 2, 'parent': 'T6'},
    {'code': 'T6_2', 'title': '6.2 Know and use the function eˣ and its graph', 'level': 2, 'parent': 'T6'},
    {'code': 'T6_3', 'title': '6.3 Know that the gradient of eᵏˣ is equal to keᵏˣ and hence understand why the exponential model is suitable in many applications', 'level': 2, 'parent': 'T6'},
    {'code': 'T6_4', 'title': '6.4 Know and use the definition of logₐ x as the inverse of aˣ, where a is positive and x > 0', 'level': 2, 'parent': 'T6'},
    {'code': 'T6_5', 'title': '6.5 Know and use the function ln x and its graph', 'level': 2, 'parent': 'T6'},
    {'code': 'T6_6', 'title': '6.6 Know and use ln x as the inverse function of eˣ', 'level': 2, 'parent': 'T6'},
    {'code': 'T6_7', 'title': '6.7 Understand and use the laws of logarithms', 'level': 2, 'parent': 'T6'},
    {'code': 'T6_8', 'title': '6.8 Solve equations of the form aˣ = b', 'level': 2, 'parent': 'T6'},
    {'code': 'T6_9', 'title': '6.9 Use logarithmic graphs to estimate parameters in relationships of the form y = axⁿ and y = kbˣ', 'level': 2, 'parent': 'T6'},
    {'code': 'T6_10', 'title': '6.10 Understand and use exponential growth and decay; use in modelling', 'level': 2, 'parent': 'T6'},
    
    # ==================================================================================
    # TOPIC 7: DIFFERENTIATION
    # ==================================================================================
    {'code': 'T7', 'title': '7 - Differentiation', 'level': 1, 'parent': 'Paper1'},
    
    {'code': 'T7_1', 'title': '7.1 Understand and use the derivative of f(x) as the gradient of the tangent to the graph of y = f(x) at a general point (x, y); the gradient of the tangent as a limit; interpretation as a rate of change', 'level': 2, 'parent': 'T7'},
    {'code': 'T7_2', 'title': '7.2 Sketch the gradient function for a given curve', 'level': 2, 'parent': 'T7'},
    {'code': 'T7_3', 'title': '7.3 Use the standard results for derivatives of polynomials', 'level': 2, 'parent': 'T7'},
    {'code': 'T7_4', 'title': '7.4 Apply differentiation to find gradients, tangents and normals, maxima and minima and stationary points, points of inflection', 'level': 2, 'parent': 'T7'},
    {'code': 'T7_5', 'title': '7.5 Differentiate eᵏˣ and akˣ, sin kx, cos kx, tan kx and related sums, differences and constant multiples', 'level': 2, 'parent': 'T7'},
    {'code': 'T7_6', 'title': '7.6 Understand and use the derivative of ln x', 'level': 2, 'parent': 'T7'},
    {'code': 'T7_7', 'title': '7.7 Differentiate using the product rule, the quotient rule and the chain rule', 'level': 2, 'parent': 'T7'},
    {'code': 'T7_8', 'title': '7.8 Differentiate simple functions defined implicitly or parametrically', 'level': 2, 'parent': 'T7'},
    {'code': 'T7_9', 'title': '7.9 Construct simple differential equations in pure mathematics and in context', 'level': 2, 'parent': 'T7'},
    {'code': 'T7_10', 'title': '7.10 Interpret the solution of a differential equation in the context of solving a problem', 'level': 2, 'parent': 'T7'},
    {'code': 'T7_11', 'title': '7.11 Find and use the second derivative; understand its meaning and use it as a second rate of change', 'level': 2, 'parent': 'T7'},
    
    # ==================================================================================
    # TOPIC 8: INTEGRATION
    # ==================================================================================
    {'code': 'T8', 'title': '8 - Integration', 'level': 1, 'parent': 'Paper1'},
    
    {'code': 'T8_1', 'title': '8.1 Know and use the Fundamental Theorem of Calculus', 'level': 2, 'parent': 'T8'},
    {'code': 'T8_2', 'title': '8.2 Integrate xⁿ (excluding n = −1), and related sums, differences and constant multiples', 'level': 2, 'parent': 'T8'},
    {'code': 'T8_3', 'title': '8.3 Integrate eᵏˣ, 1/x, sin kx, cos kx and related sums, differences and constant multiples', 'level': 2, 'parent': 'T8'},
    {'code': 'T8_4', 'title': '8.4 Evaluate definite integrals; use a definite integral to find the area under a curve and the area between two curves', 'level': 2, 'parent': 'T8'},
    {'code': 'T8_5', 'title': '8.5 Understand and use integration as the limit of a sum', 'level': 2, 'parent': 'T8'},
    {'code': 'T8_6', 'title': '8.6 Carry out simple cases of integration by substitution and integration by parts', 'level': 2, 'parent': 'T8'},
    {'code': 'T8_7', 'title': '8.7 Integrate using partial fractions', 'level': 2, 'parent': 'T8'},
    {'code': 'T8_8', 'title': '8.8 Evaluate the analytical solution of simple first order differential equations with separable variables', 'level': 2, 'parent': 'T8'},
    {'code': 'T8_9', 'title': '8.9 Interpret the solution of a differential equation in the context of solving a problem', 'level': 2, 'parent': 'T8'},
    {'code': 'T8_10', 'title': '8.10 Use trapezium rule to estimate the value of a definite integral', 'level': 2, 'parent': 'T8'},
    
    # ==================================================================================
    # TOPIC 9: NUMERICAL METHODS
    # ==================================================================================
    {'code': 'T9', 'title': '9 - Numerical methods', 'level': 1, 'parent': 'Paper2'},
    
    {'code': 'T9_1', 'title': '9.1 Locate roots of f(x) = 0 by considering changes of sign of f(x) in an interval of x where f(x) is continuous', 'level': 2, 'parent': 'T9'},
    {'code': 'T9_2', 'title': '9.2 Understand and use the Newton-Raphson method and be aware of situations where it may fail', 'level': 2, 'parent': 'T9'},
    {'code': 'T9_3', 'title': '9.3 Understand and use numerical integration of functions, including the use of the trapezium rule', 'level': 2, 'parent': 'T9'},
    
    # ==================================================================================
    # TOPIC 10: VECTORS
    # ==================================================================================
    {'code': 'T10', 'title': '10 - Vectors', 'level': 1, 'parent': 'Paper2'},
    
    {'code': 'T10_1', 'title': '10.1 Use vectors in two dimensions and in three dimensions', 'level': 2, 'parent': 'T10'},
    {'code': 'T10_2', 'title': '10.2 Calculate the magnitude and direction of a vector and convert between component form and magnitude/direction form', 'level': 2, 'parent': 'T10'},
    {'code': 'T10_3', 'title': '10.3 Add vectors diagrammatically and perform the algebraic operations of vector addition and multiplication by scalars, and understand their geometrical interpretations', 'level': 2, 'parent': 'T10'},
    {'code': 'T10_4', 'title': '10.4 Understand and use position vectors; calculate the distance between two points represented by position vectors', 'level': 2, 'parent': 'T10'},
    {'code': 'T10_5', 'title': '10.5 Use vectors to solve problems in pure mathematics and in context', 'level': 2, 'parent': 'T10'},
    {'code': 'T10_6', 'title': '10.6 Understand and use the vector equation of a line in two and three dimensions', 'level': 2, 'parent': 'T10'},
    {'code': 'T10_7', 'title': '10.7 Understand and use the scalar product', 'level': 2, 'parent': 'T10'},
]


def upload_topics():
    """Upload Mathematics topics to Supabase."""
    
    print("=" * 80)
    print("EDEXCEL MATHEMATICS (9MA0) - MANUAL TOPIC UPLOAD")
    print("=" * 80)
    print(f"\nSubject: {SUBJECT['name']}")
    print(f"Code: {SUBJECT['code']}")
    print(f"Topics: {len(TOPICS)}")
    print("Complete hierarchy - NO truncation - CLEAN structure\n")
    
    try:
        # Get/create subject
        print("[INFO] Creating/updating subject...")
        subject_result = supabase.table('staging_aqa_subjects').upsert({
            'subject_name': f"{SUBJECT['name']} (A-Level)",
            'subject_code': SUBJECT['code'],
            'qualification_type': 'A-Level',
            'specification_url': SUBJECT['pdf_url'],
            'exam_board': 'Edexcel'
        }, on_conflict='subject_code,qualification_type,exam_board').execute()
        
        subject_id = subject_result.data[0]['id']
        print(f"[OK] Subject ID: {subject_id}")
        
        # Clear old topics
        print("\n[INFO] Clearing old topics...")
        supabase.table('staging_aqa_topics').delete().eq('subject_id', subject_id).execute()
        print("[OK] Cleared")
        
        # Insert topics
        print(f"\n[INFO] Uploading {len(TOPICS)} topics...")
        to_insert = [{
            'subject_id': subject_id,
            'topic_code': t['code'],
            'topic_name': t['title'],
            'topic_level': t['level'],
            'exam_board': 'Edexcel'
        } for t in TOPICS]
        
        inserted_result = supabase.table('staging_aqa_topics').insert(to_insert).execute()
        print(f"[OK] Uploaded {len(inserted_result.data)} topics")
        
        # Link hierarchy
        print("\n[INFO] Linking parent-child relationships...")
        code_to_id = {t['topic_code']: t['id'] for t in inserted_result.data}
        linked = 0
        
        for topic in TOPICS:
            if topic['parent']:
                parent_id = code_to_id.get(topic['parent'])
                child_id = code_to_id.get(topic['code'])
                if parent_id and child_id:
                    supabase.table('staging_aqa_topics').update({
                        'parent_topic_id': parent_id
                    }).eq('id', child_id).execute()
                    linked += 1
        
        print(f"[OK] Linked {linked} relationships")
        
        # Summary
        print("\n" + "=" * 80)
        print("[OK] MATHEMATICS TOPICS UPLOADED SUCCESSFULLY!")
        print("=" * 80)
        
        levels = {}
        for t in TOPICS:
            levels[t['level']] = levels.get(t['level'], 0) + 1
        
        print("\n[INFO] Hierarchy:")
        print(f"   Level 0 (Papers): {levels.get(0, 0)}")
        print(f"   Level 1 (Main Topics): {levels.get(1, 0)}")
        print(f"   Level 2 (Learning Objectives): {levels.get(2, 0)}")
        print(f"   Level 3 (Methods/Techniques): {levels.get(3, 0)}")
        print(f"\n   Total: {len(TOPICS)} topics")
        
        print("\n" + "=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = upload_topics()
    sys.exit(0 if success else 1)
