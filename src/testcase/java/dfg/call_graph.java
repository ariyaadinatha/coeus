public class SqlInjectionLesson2 {
  public AttackResult completed(@RequestParam String query) {
    return injectableQuery(query);
  }

  protected AttackResult injectableQuery(String query) {
    try (var connection = dataSource.getConnection()) {
      Statement statement = connection.createStatement(TYPE_SCROLL_INSENSITIVE, CONCUR_READ_ONLY);
      ResultSet results = statement.executeQuery(query);
      StringBuilder output = new StringBuilder();

      results.first();
    } catch (SQLException sqle) {
      return failed(this).feedback("sql-injection.2.failed").output(sqle.getMessage()).build();
    }
  }
}
