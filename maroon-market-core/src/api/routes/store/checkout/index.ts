import { Request, Response } from "express";

/**
 * Custom Medusa API route to handle sovereign checkouts
 * Uses the SplitTenderService to allocate payments.
 */
export default async (req: Request, res: Response) => {
  const { cart_id } = req.body;

  const splitTenderService = req.scope.resolve("splitTenderService");

  try {
    // 1. Evaluate the tender distribution based on sovereign rules
    const tenderAllocation = await splitTenderService.evaluateCartTender(cart_id);

    // 2. Execute the multi-gateway transaction
    const success = await splitTenderService.executeSplitPayment(cart_id, tenderAllocation);

    if (success) {
      res.json({
        message: "Maroon Sovereign Checkout Successful",
        allocation: tenderAllocation,
        status: "COMPLETED"
      });
    } else {
      res.status(400).json({ error: "Failed to allocate funds across Split-Tender." });
    }
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};
