@RestController
public class CrossSiteScriptingLesson5a extends AssignmentEndpoint {

  public static final Predicate<String> XSS_PATTERN =
      Pattern.compile(
              ".*<script>(console\\.log|alert)\\(.*\\);?</script>.*", Pattern.CASE_INSENSITIVE)
          .asMatchPredicate();
  @Autowired UserSessionData userSessionData;

  @GetMapping("/CrossSiteScripting/attack5a")
  @ResponseBody
  public AttackResult completed(
      @RequestParam Integer QTY1,
      @RequestParam Integer QTY2,
      @RequestParam Integer QTY3,
      @RequestParam Integer QTY4,
      @RequestParam String field1,
      @RequestParam String field2) {

    double totalSale =
        QTY1.intValue() * 69.99
            + QTY2.intValue() * 27.99
            + QTY3.intValue() * 1599.99
            + QTY4.intValue() * 299.99;

    StringBuilder cart = new StringBuilder();
    cart.append("Thank you for shopping at WebGoat. <br />Your support is appreciated<hr />");
    cart.append("<p>We have charged credit card:" + field1 + "<br />");
    cart.append("                             ------------------- <br />");
    cart.append("                               $" + totalSale);

    if (XSS_PATTERN.test(field1)) {
      userSessionData.setValue("xss-reflected-5a-complete", "true");
      if (field1.toLowerCase().contains("console.log")) {
        return success(this)
            .feedback("xss-reflected-5a-success-console")
            .output(cart.toString())
            .build();
      } else {
        return success(this)
            .feedback("xss-reflected-5a-success-alert")
            .output(cart.toString())
            .build();
      }
    }
  }
}
