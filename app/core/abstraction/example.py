"""
Complete CS51 Example: Student Grade Management System
مثال كامل CS51: نظام إدارة درجات الطلاب

This example demonstrates ALL THREE programming paradigms working together
in perfect harmony, showing the difference between "programming" and
"programming well" as taught in CS51.

Architecture:
┌─────────────────────────────────────────────────────────────┐
│                  APPLICATION LAYER                          │
│  (Imperative Shell - Orchestrates everything)               │
└────────────────────┬────────────────────────────────────────┘
                     │
      ┌──────────────┼──────────────┐
      │              │              │
      ▼              ▼              ▼
┌─────────┐   ┌─────────────┐  ┌──────────┐
│FUNCTIONAL│   │OBJECT-      │  │IMPERATIVE│
│  CORE    │   │ORIENTED     │  │  SHELL   │
│          │   │             │  │          │
│Pure Logic│   │Encapsulation│  │Side      │
│Immutable │   │Protocols    │  │Effects   │
│Composable│   │Polymorphism │  │State     │
└─────────┘   └─────────────┘  └──────────┘

This is production-ready code that could change the world.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol
from uuid import uuid4

# Import our CS51 abstraction layers
from app.core.abstraction.functional import (
    pure_function,
    ImmutableList,
    Either,
    Left,
    Right,
)
from app.core.abstraction.imperative import (
    Effect,
    EffectType,
    LogEffect,
    MetricEffect,
    NotificationEffect,
    DatabaseCommandEffect,
    EffectInterpreter,
    EffectHandler,
    ImperativeShell,
    EffectBuilder,
)
from app.core.abstraction.oop import (
    Repository,
    ValueObject,
    DomainEvent,
    EventBus,
    InMemoryRepository,
    Specification,
    CompositeSpecification,
)

# ============================================================================
# LAYER 1: FUNCTIONAL CORE - Pure Business Logic
# الطبقة الوظيفية - منطق الأعمال النقي
# ============================================================================

@dataclass(frozen=True)
class GradeValue(ValueObject):
    """
    Value Object for grades (0-100).
    
    Immutable, validated, value-based equality.
    """
    value: float
    
    def __post_init__(self):
        if not 0 <= self.value <= 100:
            raise ValueError(f"Grade must be 0-100, got {self.value}")


@dataclass(frozen=True)
class StudentGrades:
    """
    Immutable student grades data.
    
    This is pure data - no behavior, just values.
    """
    id: str  # Composite key: student_id:course_id
    student_id: str
    student_name: str
    course_id: str
    course_name: str
    grades: tuple[GradeValue, ...]
    
    def __post_init__(self):
        # Validate at construction
        if not self.student_id:
            raise ValueError("Student ID required")
        if not self.course_id:
            raise ValueError("Course ID required")


# Pure functions - the heart of the functional core
@pure_function
def calculate_average(grades: tuple[GradeValue, ...]) -> float:
    """
    Calculate average grade (pure function).
    
    Referentially transparent:
    - Same input always produces same output
    - No side effects
    - Can be memoized
    - Easy to test
    """
    if not grades:
        return 0.0
    total = sum(g.value for g in grades)
    return total / len(grades)


@pure_function
def grade_to_letter(average: float) -> str:
    """Convert numeric grade to letter (pure function)."""
    if average >= 93: return "A"
    if average >= 90: return "A-"
    if average >= 87: return "B+"
    if average >= 83: return "B"
    if average >= 80: return "B-"
    if average >= 77: return "C+"
    if average >= 73: return "C"
    if average >= 70: return "C-"
    if average >= 67: return "D+"
    if average >= 63: return "D"
    if average >= 60: return "D-"
    return "F"


@pure_function
def is_passing(average: float) -> bool:
    """Check if grade is passing (pure function)."""
    return average >= 60.0


@pure_function
def is_honor_roll(average: float) -> bool:
    """Check if student qualifies for honor roll (pure function)."""
    return average >= 87.0


@pure_function
def add_grade_pure(
    student_grades: StudentGrades,
    new_grade: GradeValue
) -> StudentGrades:
    """
    Add grade to student record (pure - returns new instance).
    
    Demonstrates immutability - original is unchanged.
    """
    new_grades = student_grades.grades + (new_grade,)
    return StudentGrades(
        id=student_grades.id,
        student_id=student_grades.student_id,
        student_name=student_grades.student_name,
        course_id=student_grades.course_id,
        course_name=student_grades.course_name,
        grades=new_grades
    )


@pure_function
def calculate_grade_statistics(grades: tuple[GradeValue, ...]) -> dict[str, float]:
    """Calculate comprehensive statistics (pure function)."""
    if not grades:
        return {
            "average": 0.0,
            "min": 0.0,
            "max": 0.0,
            "median": 0.0,
            "count": 0
        }
    
    values = sorted(g.value for g in grades)
    n = len(values)
    
    return {
        "average": sum(values) / n,
        "min": min(values),
        "max": max(values),
        "median": values[n // 2] if n % 2 == 1 else (values[n//2-1] + values[n//2]) / 2,
        "count": n
    }


# ============================================================================
# LAYER 2: OBJECT-ORIENTED - Encapsulation & Protocols
# الطبقة الكائنية - التغليف والبروتوكولات
# ============================================================================

@dataclass(frozen=True)
class GradeAddedEvent:
    """Domain event: Grade was added."""
    event_id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    aggregate_id: str = ""
    student_id: str = ""
    course_id: str = ""
    grade: float = 0.0
    new_average: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "occurred_at": self.occurred_at.isoformat(),
            "aggregate_id": self.aggregate_id,
            "student_id": self.student_id,
            "course_id": self.course_id,
            "grade": self.grade,
            "new_average": self.new_average
        }


class HonorRollSpecification(CompositeSpecification[StudentGrades]):
    """
    Specification for honor roll eligibility.
    
    Encapsulates business rule as reusable object.
    """
    
    def __init__(self, min_average: float = 87.0, min_grades: int = 3):
        self.min_average = min_average
        self.min_grades = min_grades
    
    def is_satisfied_by(self, candidate: StudentGrades) -> bool:
        """Check if student qualifies for honor roll."""
        if len(candidate.grades) < self.min_grades:
            return False
        average = calculate_average(candidate.grades)
        return average >= self.min_average


class PassingGradeSpecification(CompositeSpecification[StudentGrades]):
    """Specification for passing grade."""
    
    def is_satisfied_by(self, candidate: StudentGrades) -> bool:
        """Check if student is passing."""
        if not candidate.grades:
            return False
        average = calculate_average(candidate.grades)
        return is_passing(average)


class StudentGradesRepository(Protocol):
    """
    Protocol for student grades repository.
    
    Abstraction barrier - implementations can vary.
    """
    
    async def find_by_student_and_course(
        self,
        student_id: str,
        course_id: str
    ) -> StudentGrades | None:
        """Find grades for student in course."""
        ...
    
    async def save(self, grades: StudentGrades) -> None:
        """Save student grades."""
        ...
    
    async def find_all_by_course(self, course_id: str) -> list[StudentGrades]:
        """Find all student grades for a course."""
        ...


class GradingPolicy:
    """
    Encapsulates grading policies.
    
    Demonstrates encapsulation - internal details hidden.
    """
    
    def __init__(
        self,
        passing_threshold: float = 60.0,
        honor_threshold: float = 87.0,
        notification_threshold: float = 85.0
    ):
        self._passing_threshold = passing_threshold
        self._honor_threshold = honor_threshold
        self._notification_threshold = notification_threshold
    
    def requires_notification(self, old_avg: float, new_avg: float) -> bool:
        """Determine if grade change requires notification."""
        # Crossed notification threshold
        if old_avg < self._notification_threshold <= new_avg:
            return True
        # Dropped below passing
        if old_avg >= self._passing_threshold > new_avg:
            return True
        # Achieved honor roll
        if old_avg < self._honor_threshold <= new_avg:
            return True
        return False
    
    def get_notification_message(self, grades: StudentGrades) -> str:
        """Generate notification message based on performance."""
        average = calculate_average(grades.grades)
        letter = grade_to_letter(average)
        
        if average >= self._honor_threshold:
            return (f"Congratulations {grades.student_name}! "
                   f"You've achieved Honor Roll status in {grades.course_name} "
                   f"with an average of {average:.1f} ({letter}).")
        elif average < self._passing_threshold:
            return (f"Attention {grades.student_name}: "
                   f"Your grade in {grades.course_name} is currently {average:.1f} ({letter}). "
                   f"Please schedule a meeting with your instructor.")
        else:
            return (f"Grade update for {grades.student_name} in {grades.course_name}: "
                   f"Current average is {average:.1f} ({letter}).")


# ============================================================================
# LAYER 3: IMPERATIVE SHELL - Side Effects & Orchestration
# الغلاف الإجرائي - التأثيرات الجانبية والتنسيق
# ============================================================================

class GradeManagementService:
    """
    Application service that orchestrates the use case.
    
    This is the ONLY place where side effects occur.
    Pure business logic is in functional core.
    Object management is in OOP layer.
    """
    
    def __init__(
        self,
        repository: StudentGradesRepository,
        event_bus: EventBus,
        grading_policy: GradingPolicy,
        shell: ImperativeShell
    ):
        self._repository = repository
        self._event_bus = event_bus
        self._grading_policy = grading_policy
        self._shell = shell
    
    async def add_grade(
        self,
        student_id: str,
        course_id: str,
        grade_value: float
    ) -> Either[str, StudentGrades]:
        """
        Add a grade to student's record.
        
        This method demonstrates the three-layer architecture:
        1. Imperative orchestration (this method)
        2. Pure functional logic (calculate_average, etc.)
        3. OOP encapsulation (repository, policy, events)
        
        Returns:
            Either[error_message, updated_grades]
        """
        # Build effects declaratively
        effects = EffectBuilder()
        
        try:
            # Step 1: Log start (side effect)
            effects.log(
                f"Adding grade for student {student_id} in course {course_id}",
                level="INFO",
                student_id=student_id,
                course_id=course_id,
                grade=grade_value
            )
            
            # Execute log effect
            await self._shell.execute_effects(effects.build())
            effects = EffectBuilder()  # Reset
            
            # Step 2: Validate input (pure)
            try:
                grade = GradeValue(grade_value)
            except ValueError as e:
                effects.log(f"Invalid grade value: {e}", level="ERROR")
                await self._shell.execute_effects(effects.build())
                return Left(str(e))
            
            # Step 3: Fetch current state (side effect)
            current_grades = await self._repository.find_by_student_and_course(
                student_id, course_id
            )
            
            if not current_grades:
                return Left(f"No record found for student {student_id} in course {course_id}")
            
            # Calculate old average (pure)
            old_average = calculate_average(current_grades.grades)
            
            # Step 4: Calculate new state (PURE - no side effects!)
            updated_grades = add_grade_pure(current_grades, grade)
            new_average = calculate_average(updated_grades.grades)
            
            # Step 5: Check if notification needed (pure + encapsulated logic)
            needs_notification = self._grading_policy.requires_notification(
                old_average, new_average
            )
            
            # Step 6: Save new state (side effect)
            await self._repository.save(updated_grades)
            
            # Step 7: Record metric (side effect)
            effects.metric(
                "grade_added",
                1.0,
                course=course_id,
                student=student_id
            )
            
            effects.metric(
                "student_average",
                new_average,
                course=course_id,
                student=student_id
            )
            
            await self._shell.execute_effects(effects.build())
            effects = EffectBuilder()
            
            # Step 8: Publish domain event (side effect)
            event = GradeAddedEvent(
                aggregate_id=f"{student_id}:{course_id}",
                student_id=student_id,
                course_id=course_id,
                grade=grade_value,
                new_average=new_average
            )
            await self._event_bus.publish(event)
            
            # Step 9: Send notification if needed (side effect)
            if needs_notification:
                message = self._grading_policy.get_notification_message(updated_grades)
                effects.notify(
                    channel="email",
                    recipient=f"student:{student_id}",
                    message=message
                )
                
                effects.log(
                    f"Notification sent to student {student_id}",
                    level="INFO"
                )
            
            # Execute remaining effects
            await self._shell.execute_effects(effects.build())
            
            # Step 10: Return success (Either monad)
            return Right(updated_grades)
            
        except Exception as e:
            # Error handling (side effect)
            effects.log(
                f"Error adding grade: {e}",
                level="ERROR",
                student_id=student_id,
                course_id=course_id
            )
            await self._shell.execute_effects(effects.build())
            return Left(f"Failed to add grade: {e}")
    
    async def get_honor_roll(self, course_id: str) -> list[StudentGrades]:
        """
        Get honor roll students for a course.
        
        Demonstrates specification pattern + functional filtering.
        """
        # Fetch all students (side effect)
        all_students = await self._repository.find_all_by_course(course_id)
        
        # Filter using specification (pure logic + OOP)
        honor_spec = HonorRollSpecification()
        honor_students = [
            student for student in all_students
            if honor_spec.is_satisfied_by(student)
        ]
        
        # Log result (side effect)
        effects = (EffectBuilder()
            .log(
                f"Honor roll for course {course_id}: {len(honor_students)} students",
                level="INFO",
                course_id=course_id,
                count=len(honor_students)
            )
            .metric("honor_roll_count", float(len(honor_students)), course=course_id))
        
        await self._shell.execute_effects(effects.build())
        
        return honor_students
    
    async def get_grade_statistics(
        self,
        student_id: str,
        course_id: str
    ) -> Either[str, dict]:
        """
        Get comprehensive grade statistics.
        
        Pure calculation with imperative I/O.
        """
        # Fetch grades (side effect)
        grades = await self._repository.find_by_student_and_course(
            student_id, course_id
        )
        
        if not grades:
            return Left("Student grades not found")
        
        # Calculate statistics (pure)
        stats = calculate_grade_statistics(grades.grades)
        stats["letter_grade"] = grade_to_letter(stats["average"])
        stats["is_passing"] = is_passing(stats["average"])
        stats["is_honor_roll"] = is_honor_roll(stats["average"])
        
        return Right(stats)


# ============================================================================
# EXAMPLE USAGE - Demonstrating All Three Paradigms
# مثال الاستخدام - إظهار الأنماط الثلاثة
# ============================================================================

async def demonstrate_cs51_principles():
    """
    Complete demonstration of CS51 principles in action.
    
    Shows how functional, imperative, and OOP paradigms work together.
    """
    
    print("=" * 80)
    print("CS51 - Abstraction and Design in Computation")
    print("Complete Example: Student Grade Management")
    print("=" * 80)
    
    # Setup (imperative)
    repository = InMemoryRepository()
    event_bus = EventBus()
    grading_policy = GradingPolicy()
    shell = ImperativeShell()
    
    # Register effect handlers (would be real implementations in production)
    class MockEffectHandler:
        async def handle(self, effect: Effect) -> None:
            print(f"  [Effect] {effect.describe()}")
    
    shell.register_handler(EffectType.LOG, MockEffectHandler())
    shell.register_handler(EffectType.METRIC, MockEffectHandler())
    shell.register_handler(EffectType.NOTIFICATION, MockEffectHandler())
    
    # Create service
    service = GradeManagementService(
        repository=repository,
        event_bus=event_bus,
        grading_policy=grading_policy,
        shell=shell
    )
    
    # Create initial student records
    initial_grades = StudentGrades(
        id="S001:CS51",
        student_id="S001",
        student_name="Alice Johnson",
        course_id="CS51",
        course_name="Abstraction and Design",
        grades=(GradeValue(85.0), GradeValue(88.0))
    )
    
    await repository.save(initial_grades)
    
    print("\n1. FUNCTIONAL CORE - Pure Calculations")
    print("-" * 80)
    avg = calculate_average(initial_grades.grades)
    letter = grade_to_letter(avg)
    print(f"  Average: {avg:.1f}")
    print(f"  Letter Grade: {letter}")
    print(f"  Passing: {is_passing(avg)}")
    print(f"  Honor Roll: {is_honor_roll(avg)}")
    
    print("\n2. OBJECT-ORIENTED - Specifications & Encapsulation")
    print("-" * 80)
    honor_spec = HonorRollSpecification()
    passing_spec = PassingGradeSpecification()
    print(f"  Meets Honor Roll Spec: {honor_spec.is_satisfied_by(initial_grades)}")
    print(f"  Meets Passing Spec: {passing_spec.is_satisfied_by(initial_grades)}")
    
    print("\n3. IMPERATIVE SHELL - Side Effects & Orchestration")
    print("-" * 80)
    print("  Adding new grade (92.0)...")
    result = await service.add_grade("S001", "CS51", 92.0)
    
    match result:
        case Right(updated_grades):
            new_avg = calculate_average(updated_grades.grades)
            print(f"  ✓ Success! New average: {new_avg:.1f}")
        case Left(error):
            print(f"  ✗ Error: {error}")
    
    print("\n4. COMBINED POWER - All Paradigms Working Together")
    print("-" * 80)
    stats_result = await service.get_grade_statistics("S001", "CS51")
    
    match stats_result:
        case Right(stats):
            print("  Grade Statistics:")
            for key, value in stats.items():
                print(f"    {key}: {value}")
        case Left(error):
            print(f"  ✗ Error: {error}")
    
    print("\n" + "=" * 80)
    print("This demonstrates the power of CS51 principles:")
    print("  • Functional: Pure, testable, composable logic")
    print("  • OOP: Encapsulation, protocols, polymorphism")
    print("  • Imperative: Controlled side effects, orchestration")
    print("  • Result: Clean, maintainable, world-class architecture")
    print("=" * 80)


if __name__ == "__main__":
    import asyncio
    asyncio.run(demonstrate_cs51_principles())
