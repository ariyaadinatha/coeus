public class SqlInjectionLesson5a extends AssignmentEndpoint {
  public AttackResult completed(
      @RequestParam String account, @RequestParam String operator, @RequestParam String injection) {
    return injectableQuery(account + " " + operator + " " + injection);
  }

  protected AttackResult injectableQuery(String accountName) {
    String query = "";
    try (Connection connection = dataSource.getConnection()) {
      query =
          "SELECT * FROM user_data WHERE first_name = 'John' and last_name = '" + accountName + "'";
      try (Statement statement =
          connection.createStatement(
              ResultSet.TYPE_SCROLL_INSENSITIVE, ResultSet.CONCUR_UPDATABLE)) {
        ResultSet results = statement.executeQuery(query);
      } catch (SQLException sqle) {
      }
    } catch (Exception e) {
    }
  }
}
