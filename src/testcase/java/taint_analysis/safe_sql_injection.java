public class SqlInjectionChallengeLogin extends AssignmentEndpoint {
  public AttackResult login(
      @RequestParam String username_login, @RequestParam String password_login) throws Exception {
    try (var connection = dataSource.getConnection()) {
      var statement =
          connection.prepareStatement(
              "select password from sql_challenge_users where userid = " + username_login + " and password = ?");
      statement.setString(1, password_login);
      var resultSet = statement.executeQuery();
    }
  }
}
