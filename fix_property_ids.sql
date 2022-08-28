UPDATE `sales` SET `property_id` = REPLACE(`property_id`, '[', '') WHERE `property_id` LIKE "%[%";
UPDATE `sales` SET `property_id` = REPLACE(`property_id`, ']', '') WHERE `property_id` LIKE "%]%";
UPDATE `sales` SET `property_id` = REPLACE(`property_id`, '{', '') WHERE `property_id` LIKE "%{%";
UPDATE `sales` SET `property_id` = REPLACE(`property_id`, '}', '') WHERE `property_id` LIKE "%}%";
