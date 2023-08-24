public class Assignment5 extends AssignmentEndpoint {
  public AttackResult login(
      @RequestParam String username_login, @RequestParam String password_login) throws Exception {
    try (var connection = dataSource.getConnection()) {
      PreparedStatement statement =
          connection.prepareStatement(
              "select password from challenge_users where userid = '"
                  + username_login
                  + "' and password = '"
                  + password_login
                  + "'");
      ResultSet resultSet = statement.executeQuery();
    }
  }
}
