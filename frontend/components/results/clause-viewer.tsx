"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { AlertCircle, CheckCircle2, FileText, AlertTriangle } from "lucide-react";
import { ClauseAnalysis, ClauseFilter } from "@/lib/types";
import { getRiskLevelColor } from "@/lib/utils";

interface ClauseViewerProps {
  clauses: ClauseAnalysis[];
}

export function ClauseViewer({ clauses }: ClauseViewerProps) {
  const [filter, setFilter] = useState<ClauseFilter>("all");

  const filteredClauses = clauses.filter((clause) => {
    if (filter === "all") return true;
    if (filter === "non-compliant") return clause.compliance_status === "Non-Compliant";
    if (filter === "critical")
      return clause.risk_level === "Critical" || clause.risk_level === "High";
    return true;
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "Compliant":
        return <CheckCircle2 className="h-5 w-5 text-green-600" />;
      case "Non-Compliant":
        return <AlertCircle className="h-5 w-5 text-red-600" />;
      default:
        return <AlertTriangle className="h-5 w-5 text-yellow-600" />;
    }
  };

  const getStatusBadge = (status: string) => {
    const variants: Record<string, "success" | "destructive" | "warning"> = {
      Compliant: "success",
      "Non-Compliant": "destructive",
      "Needs Review": "warning",
    };
    return (
      <Badge variant={variants[status] || "default"}>
        {status}
      </Badge>
    );
  };

  return (
    <div className="space-y-4">
      {/* Filter Buttons */}
      <div className="flex flex-wrap gap-2">
        <Button
          variant={filter === "all" ? "default" : "outline"}
          size="sm"
          onClick={() => setFilter("all")}
        >
          All Clauses ({clauses.length})
        </Button>
        <Button
          variant={filter === "non-compliant" ? "default" : "outline"}
          size="sm"
          onClick={() => setFilter("non-compliant")}
        >
          Non-Compliant (
          {clauses.filter((c) => c.compliance_status === "Non-Compliant").length})
        </Button>
        <Button
          variant={filter === "critical" ? "default" : "outline"}
          size="sm"
          onClick={() => setFilter("critical")}
        >
          Critical/High Risk (
          {clauses.filter((c) => c.risk_level === "Critical" || c.risk_level === "High").length})
        </Button>
      </div>

      {/* Clauses List */}
      {filteredClauses.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <FileText className="mx-auto h-12 w-12 text-gray-400" />
            <p className="mt-4 text-sm font-medium text-gray-900">
              No clauses match this filter
            </p>
          </CardContent>
        </Card>
      ) : (
        <Accordion type="single" collapsible className="space-y-2">
          {filteredClauses.map((clause, index) => (
            <AccordionItem
              key={clause.clause_number || index}
              value={`clause-${clause.clause_number || index}`}
              className="rounded-lg border bg-white"
            >
              <AccordionTrigger className="px-6 hover:no-underline">
                <div className="flex w-full items-center justify-between pr-4">
                  <div className="flex items-center gap-4">
                    {getStatusIcon(clause.compliance_status)}
                    <div className="text-left">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold">
                          Clause {clause.clause_number}
                        </span>
                        <Badge variant="outline" className="text-xs">
                          {clause.clause_type}
                        </Badge>
                      </div>
                      <p className="mt-1 line-clamp-1 text-sm font-normal text-gray-600">
                        {clause.clause_text ? clause.clause_text.substring(0, 100) + "..." : "No text available"}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className={getRiskLevelColor(clause.risk_level)}>
                      {clause.risk_level}
                    </Badge>
                    {getStatusBadge(clause.compliance_status)}
                  </div>
                </div>
              </AccordionTrigger>
              <AccordionContent className="px-6 pb-6">
                <div className="space-y-4 pt-4">
                  {/* Original Text */}
                  {clause.clause_text && (
                    <div>
                      <h4 className="mb-2 text-sm font-semibold text-gray-900">
                        Original Text
                      </h4>
                      <div className="rounded-lg bg-gray-50 p-4 text-sm text-gray-700">
                        {clause.clause_text}
                      </div>
                    </div>
                  )}

                  {/* Issues */}
                  {clause.issues && clause.issues.length > 0 && (
                    <div>
                      <h4 className="mb-2 text-sm font-semibold text-gray-900">
                        Issues Identified
                      </h4>
                      <ul className="space-y-2">
                        {clause.issues.map((issue, index) => (
                          <li
                            key={index}
                            className="flex gap-2 text-sm text-gray-700"
                          >
                            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-red-600" />
                            <span>
                              {typeof issue === 'string'
                                ? issue
                                : issue.issue_description || JSON.stringify(issue)}
                            </span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Recommendations */}
                  {clause.recommendations && clause.recommendations.length > 0 && (
                    <div>
                      <h4 className="mb-2 text-sm font-semibold text-gray-900">
                        Recommendations
                      </h4>
                      <ul className="space-y-2">
                        {clause.recommendations.map((rec, index) => (
                          <li
                            key={index}
                            className="flex gap-2 text-sm text-gray-700"
                          >
                            <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-green-600" />
                            <span>
                              {typeof rec === 'string'
                                ? rec
                                : rec.recommendation || JSON.stringify(rec)}
                            </span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Suggested Text */}
                  {clause.suggested_text && (
                    <div>
                      <h4 className="mb-2 text-sm font-semibold text-gray-900">
                        Suggested Alternative
                      </h4>
                      <div className="rounded-lg bg-green-50 p-4 text-sm text-gray-700">
                        {clause.suggested_text}
                      </div>
                    </div>
                  )}

                  {/* Policy References */}
                  {clause.policy_references && clause.policy_references.length > 0 && (
                    <div>
                      <h4 className="mb-2 text-sm font-semibold text-gray-900">
                        Policy References
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {clause.policy_references.map((ref, index) => (
                          <Badge key={index} variant="outline">
                            <FileText className="mr-1 h-3 w-3" />
                            {typeof ref === 'string' ? ref : ref.policy_name || JSON.stringify(ref)}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      )}
    </div>
  );
}
