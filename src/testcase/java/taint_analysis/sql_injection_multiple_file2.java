public class SqlInjectionLesson6a extends AssignmentEndpoint {
  public AttackResult injectableQuery(String accountName) {
    String query = "";
    try (Connection connection = dataSource.getConnection()) {
      boolean usedUnion = true;
      query = "SELECT * FROM user_data WHERE last_name = '" + accountName + "'";
      try (Statement statement =
          connection.createStatement(
              ResultSet.TYPE_SCROLL_INSENSITIVE, ResultSet.CONCUR_READ_ONLY)) {
        ResultSet results = statement.executeQuery(query);
      } catch (SQLException sqle) {
      }
    } catch (Exception e) {
    }
  }
}
