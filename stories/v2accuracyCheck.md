[Table of Contents](index.html)
## Session: Accuracy Check

**Date:** 2025-09-21
## Starting Position
I have all the code in place to take care of the financial and inventory logic but it needs a thorough accuracy check. After running though a few games to collect statistical measures to demonstrate in the dashboard I want to be sure the numbers are right.
* **Cash:** $50,000
* **Core principles for this game session:** Starting with no inventory and buying 3 types of mechanical keyboard switches. Two others will unlock later in the game after revenue milestones.<br>
* **Market Condition:** 
The current condition is tough. My last play-through i ended with 40k in cash and 18k in inventory after 18+ months. More vendors and order size discounts need to be created. More items need to be added. Winning should be rewarded with better margins.<br>
For now i want to check that the sale record is true and accurate in the both the react frontend and business intelligence dashboards. This will be my record of this investigation.

## Key Events & Decisions

1.  **The Gamble:** Bought as many units as it took to keep all unlocked products in stock for sale.
2.  **Price Adjustment:** I did not change the price. This play-through is to test the accuracy of the sales model.
3.  **The Payoff:** The most important thing is that debits and credits are being recorded accurately and balance to zero.

## Outcome

* **Ending Cash:** $1,045,861.82 with almost $140k in inventory.
* **Lessons Learned:** Winning is possible. I needed a better way to track outstanding orders. Financial logic is correct.
* **Notes:**<br>
1/1/25<br>
I ordered 1000 each of browns, and whites from my 3 day vendor.<br>
1/8/25<br>
Sales began, 7 days in.<br>
I went ahead and 3000 reds from my 25 day vendor.<br>
I brought 1500 reds and browns from my 6 day vendor.<br>
While orders were being placed, i went ahead and bought 3000 browns, reds, and whites from my 20 day vendor.<br>
1/29/25<br>
All items are in stock, its kind of hard to know what orders are outstanding.<br>
3/5/25<br>
I ordered 3000 whites from my 20 day vendor, these had dropped to about 2000.<br>
3/26/25<br>
After realizing how hard it was to know what was ordered I added "pending deliveries" under the "Bills due soon". These also drop down and show the items on the order now.<br>
I ordered a bunch more switches from the low price vendors to be sure I kept these 3 items in stock at their low prices.<br>
6/11/25<br>
The blues finally unlocked. I ordered a bunch from different vendors for speed and price.<br>
8/06/25<br>
The blacks finally unlocked. I ordered from different vendors for speed and price.<br>
Company equity has started to increase.<br>
Beyond this point..<br>
I kept all items in stock. I ordered way in advance and started advancing time 60 days at a time.<br>
Total company equity grew to $117k and I was winning the game. I checked credits vs debits and they equal out to $0. The numbers in my dashboard match those straight from MySQL Workbench.<br>
Several bugs were caught and worked though this run.<br>
6/25/2039<br>
Continued playing getting to the point of keeping around 150,000 of each item, and advancing time 360 days at a time. I showed that the system is robust, books remain correct, and to see things get stressed with an ever-growing database<br>
Ended with over $1,000,000

