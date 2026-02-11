------------------------ MODULE mission_lifecycle ------------------------

EXTENDS Integers, Sequences, FiniteSets

CONSTANTS
    MissionIDs,
    Tasks,
    CriticalTasks,
    MaxRetries

VARIABLES
    mission_status,
    task_status,
    task_retries,
    evidence

-----------------------------------------------------------------------------

(* Possible Status Values *)
Status == {"pending", "running", "success", "partial_success", "failed"}

(* Type Invariant: Ensures variables always hold valid values *)
TypeOK ==
    /\ mission_status \in [MissionIDs -> Status]
    /\ task_status \in [MissionIDs -> [Tasks -> Status]]
    /\ task_retries \in [MissionIDs -> [Tasks -> 0..MaxRetries]]
    /\ evidence \in [MissionIDs -> [Tasks -> BOOLEAN]]

(* Initial State *)
Init ==
    /\ mission_status = [m \in MissionIDs |-> "pending"]
    /\ task_status = [m \in MissionIDs |-> [t \in Tasks |-> "pending"]]
    /\ task_retries = [m \in MissionIDs |-> [t \in Tasks |-> 0]]
    /\ evidence = [m \in MissionIDs |-> [t \in Tasks |-> FALSE]]

-----------------------------------------------------------------------------

(* Actions *)

(* Start a Mission *)
StartMission(m) ==
    /\ mission_status[m] = "pending"
    /\ mission_status' = [mission_status EXCEPT ![m] = "running"]
    /\ UNCHANGED <<task_status, task_retries, evidence>>

(* Start a Task *)
StartTask(m, t) ==
    /\ mission_status[m] = "running"
    /\ task_status[m][t] = "pending"
    /\ task_status' = [task_status EXCEPT ![m][t] = "running"]
    /\ UNCHANGED <<mission_status, task_retries, evidence>>

(* Task Success: Must produce evidence *)
TaskSucceeds(m, t) ==
    /\ task_status[m][t] = "running"
    /\ task_status' = [task_status EXCEPT ![m][t] = "success"]
    /\ evidence' = [evidence EXCEPT ![m][t] = TRUE]  (* CRITICAL: Success implies Evidence *)
    /\ UNCHANGED <<mission_status, task_retries>>

(* Task Failure: Can retry or fail permanently *)
TaskFails(m, t) ==
    /\ task_status[m][t] = "running"
    /\ IF task_retries[m][t] < MaxRetries
       THEN
            /\ task_retries' = [task_retries EXCEPT ![m][t] = @ + 1]
            /\ task_status' = [task_status EXCEPT ![m][t] = "pending"] (* Retry *)
       ELSE
            /\ task_status' = [task_status EXCEPT ![m][t] = "failed"]
            /\ UNCHANGED task_retries
    /\ UNCHANGED <<mission_status, evidence>>

(* Complete Mission: Check all tasks *)
CompleteMission(m) ==
    /\ mission_status[m] = "running"
    /\ \A t \in Tasks : task_status[m][t] \in {"success", "failed"}
    /\ LET
        all_success == \A t \in Tasks : task_status[m][t] = "success"
        critical_failure == \E t \in CriticalTasks : task_status[m][t] = "failed"
       IN
        IF critical_failure
        THEN mission_status' = [mission_status EXCEPT ![m] = "failed"]
        ELSE IF all_success
             THEN mission_status' = [mission_status EXCEPT ![m] = "success"]
             ELSE mission_status' = [mission_status EXCEPT ![m] = "partial_success"]
    /\ UNCHANGED <<task_status, task_retries, evidence>>

-----------------------------------------------------------------------------

(* Specification *)
Next ==
    \E m \in MissionIDs :
        \/ StartMission(m)
        \/ \E t \in Tasks : StartTask(m, t)
        \/ \E t \in Tasks : TaskSucceeds(m, t)
        \/ \E t \in Tasks : TaskFails(m, t)
        \/ CompleteMission(m)

Spec == Init /\ [][Next]_<<mission_status, task_status, task_retries, evidence>>

-----------------------------------------------------------------------------

(* Invariants (Safety Properties) *)

(* 1. No Success Without Evidence *)
NoSuccessWithoutEvidence ==
    \A m \in MissionIDs :
        (mission_status[m] = "success") =>
            (\A t \in Tasks : evidence[m][t] = TRUE)

(* 2. No Silent Failure (If critical task failed, mission cannot be success) *)
NoSilentFailure ==
    \A m \in MissionIDs :
        (\E t \in CriticalTasks : task_status[m][t] = "failed") =>
            (mission_status[m] /= "success")

(* 3. Partial Success Definition *)
PartialSuccessCorrectness ==
    \A m \in MissionIDs :
        (mission_status[m] = "partial_success") =>
            (/\ \A t \in CriticalTasks : task_status[m][t] = "success"
             /\ \E t \in Tasks : task_status[m][t] = "failed")

=============================================================================
