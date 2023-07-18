public class SqlOnlyInputValidation extends AssignmentEndpoint {
  public AttackResult attack(@RequestParam("userid_sql_only_input_validation") String userId) {
    AttackResult attackResult = lesson6a.injectableQuery(userId);
  }
}
